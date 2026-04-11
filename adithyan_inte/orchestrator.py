"""
orchestrator.py
---------------
Core pipeline coordinator for Smartilee.

For every inbound message this module:
  1. Calls the AI backend /analyze endpoint.
  2. Writes the conversation record to Supabase.
  3. Routes the AI action to the appropriate handler
     (auto_reply | upsell | handoff | schedule_followup).
  4. Returns the response payload to the caller (app.py).
"""

import os
import logging
from datetime import datetime, timezone

import requests

from supabase_client import supabase
from messaging import send_outbound_message
from handoff import handle_handoff

logger = logging.getLogger(__name__)

# ── AI backend base URL (runs separately; see ai_backend/) ──────────────────
AI_BACKEND_URL: str = os.getenv("AI_BACKEND_URL", "http://localhost:5001")


# ═══════════════════════════════════════════════════════════════════════════
# Public entry point
# ═══════════════════════════════════════════════════════════════════════════

def process_message(phone_number: str, message_text: str, source: str) -> dict:
    """
    Full orchestration pipeline for one inbound message.

    Args:
        phone_number: Sender's phone number (unique customer key).
        message_text: Raw message content.
        source:       'web' | 'whatsapp'

    Returns:
        dict with keys: status, action, response (optional), handoff_id (optional).
    """
    # ── 1. Handoff guard ─────────────────────────────────────────────────
    customer = _get_or_create_customer(phone_number)

    if customer.get("is_handoff_active"):
        logger.info("Handoff active for %s — logging message, skipping AI.", phone_number)
        _log_conversation(
            customer_id=customer["id"],
            phone_number=phone_number,
            message_text=message_text,
            direction="inbound",
            source=source,
            ai_metadata={"skipped": "handoff_active"},
        )
        return {"status": "ok", "action": "handoff_active", "response": None}

    # ── 2. AI analysis ───────────────────────────────────────────────────
    ai_result = _call_ai_analyze(phone_number, message_text)

    intent = ai_result.get("intent", "general")
    sentiment = ai_result.get("sentiment", "neutral")
    action = ai_result.get("action", "auto_reply")
    churn_score = ai_result.get("churn_score", 0.0)
    language = ai_result.get("language", "en")

    # ── 3. Log inbound message + AI metadata ─────────────────────────────
    _log_conversation(
        customer_id=customer["id"],
        phone_number=phone_number,
        message_text=message_text,
        direction="inbound",
        source=source,
        ai_metadata={
            "intent": intent,
            "sentiment": sentiment,
            "action": action,
            "churn_score": churn_score,
            "language": language,
        },
    )

    # Optionally update churn score on the customer profile
    _update_churn_score(customer["id"], churn_score)

    # ── 4. Action routing ────────────────────────────────────────────────
    if action == "auto_reply":
        return _handle_auto_reply(phone_number, message_text, customer, ai_result)

    if action == "upsell":
        return _handle_upsell(phone_number, message_text, customer, ai_result)

    if action == "handoff":
        return _handle_handoff_action(phone_number, customer, intent)

    if action == "schedule_followup":
        return _handle_schedule_followup(phone_number, customer, message_text, ai_result)

    # Fallback — treat unknown actions as auto_reply
    logger.warning("Unknown action '%s' — falling back to auto_reply.", action)
    return _handle_auto_reply(phone_number, message_text, customer, ai_result)


# ═══════════════════════════════════════════════════════════════════════════
# Action handlers
# ═══════════════════════════════════════════════════════════════════════════

def _handle_auto_reply(
    phone_number: str, message_text: str, customer: dict, ai_result: dict
) -> dict:
    """Calls /generate-reply and returns the generated text."""
    reply = _call_generate_reply(phone_number, message_text, ai_result)

    send_outbound_message(
        recipient=phone_number,
        message=reply,
        message_type="auto_reply",
        customer_id=customer.get("id"),
    )

    # Log the outbound reply (persisted inside send_outbound_message)
    return {"status": "ok", "action": "auto_reply", "response": reply}


def _handle_upsell(
    phone_number: str, message_text: str, customer: dict, ai_result: dict
) -> dict:
    """Calls /upsell and returns the product recommendation."""
    recommendation = _call_upsell(phone_number, message_text, ai_result)

    send_outbound_message(
        recipient=phone_number,
        message=recommendation,
        message_type="upsell",
        customer_id=customer.get("id"),
    )

    return {"status": "ok", "action": "upsell", "response": recommendation}


def _handle_handoff_action(
    phone_number: str, customer: dict, trigger_reason: str
) -> dict:
    """Delegates to the handoff module."""
    result = handle_handoff(
        phone_number=phone_number,
        trigger_reason=f"AI intent: {trigger_reason}",
    )
    return {
        "status": "ok",
        "action": "handoff",
        "handoff_id": result.get("handoff_id"),
    }


def _handle_schedule_followup(
    phone_number: str, customer: dict, message_text: str, ai_result: dict
) -> dict:
    """Inserts a row into the `followups` table for later processing."""
    payload = {
        "customer_id": customer["id"],
        "phone_number": phone_number,
        "trigger_reason": "AI recommended follow-up",
        "original_message": message_text,
        "ai_metadata": ai_result,
        "status": "pending",
        "scheduled_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        supabase.table("followups").insert(payload).execute()
        logger.info("Follow-up scheduled for %s.", phone_number)
    except Exception as exc:
        logger.error("Failed to schedule follow-up for %s: %s", phone_number, exc)

    return {"status": "ok", "action": "schedule_followup", "response": None}


# ═══════════════════════════════════════════════════════════════════════════
# AI backend callers
# ═══════════════════════════════════════════════════════════════════════════

def _call_ai_analyze(phone_number: str, message_text: str) -> dict:
    """
    POST /analyze  →  {intent, sentiment, action, churn_score, language}
    Falls back to a safe default dict on failure so the pipeline never crashes.
    """
    try:
        response = requests.post(
            f"{AI_BACKEND_URL}/analyze",
            json={"phone_number": phone_number, "message": message_text},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error("AI /analyze call failed: %s", exc)
        return {
            "intent": "general",
            "sentiment": "neutral",
            "action": "auto_reply",
            "churn_score": 0.0,
            "language": "en",
        }


def _call_generate_reply(
    phone_number: str, message_text: str, ai_result: dict
) -> str:
    """POST /generate-reply  →  reply string."""
    try:
        response = requests.post(
            f"{AI_BACKEND_URL}/generate-reply",
            json={
                "phone_number": phone_number,
                "message": message_text,
                "ai_context": ai_result,
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json().get("reply", "Thank you for your message! We'll get back to you shortly.")
    except requests.RequestException as exc:
        logger.error("AI /generate-reply call failed: %s", exc)
        return "Thank you for reaching out! Our team will respond shortly."


def _call_upsell(phone_number: str, message_text: str, ai_result: dict) -> str:
    """POST /upsell  →  recommendation string."""
    try:
        response = requests.post(
            f"{AI_BACKEND_URL}/upsell",
            json={
                "phone_number": phone_number,
                "message": message_text,
                "ai_context": ai_result,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("recommendation", "We have some great options for you!")
    except requests.RequestException as exc:
        logger.error("AI /upsell call failed: %s", exc)
        return "We have some exciting offers that might interest you!"


# ═══════════════════════════════════════════════════════════════════════════
# Supabase helpers
# ═══════════════════════════════════════════════════════════════════════════

def _get_or_create_customer(phone_number: str) -> dict:
    """
    Fetches the customer by phone number.
    Creates a minimal profile if they don't exist yet.
    """
    try:
        result = (
            supabase.table("customers")
            .select("id, name, is_handoff_active, churn_score")
            .eq("phone_number", phone_number)
            .maybe_single()
            .execute()
        )
        if result.data:
            return result.data

        # New customer — create a minimal profile
        insert_result = (
            supabase.table("customers")
            .insert(
                {
                    "phone_number": phone_number,
                    "name": phone_number,  # overwritten when real name is known
                    "is_handoff_active": False,
                    "churn_score": 0.0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .execute()
        )
        logger.info("New customer profile created for %s.", phone_number)
        return insert_result.data[0]

    except Exception as exc:
        logger.error("Error in _get_or_create_customer for %s: %s", phone_number, exc)
        # Return a safe fallback so the pipeline can continue
        return {"id": None, "is_handoff_active": False, "churn_score": 0.0}


def _log_conversation(
    customer_id: str | None,
    phone_number: str,
    message_text: str,
    direction: str,
    source: str,
    ai_metadata: dict,
) -> None:
    """Writes a conversation row to the `conversations` table."""
    try:
        supabase.table("conversations").insert(
            {
                "customer_id": customer_id,
                "phone_number": phone_number,
                "message_text": message_text,
                "direction": direction,
                "source": source,
                "ai_metadata": ai_metadata,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
    except Exception as exc:
        logger.error("Failed to log conversation: %s", exc)


def _update_churn_score(customer_id: str | None, churn_score: float) -> None:
    """Updates the customer's churn score if it changed."""
    if not customer_id:
        return
    try:
        supabase.table("customers").update(
            {"churn_score": churn_score}
        ).eq("id", customer_id).execute()
    except Exception as exc:
        logger.warning("Failed to update churn score for %s: %s", customer_id, exc)
