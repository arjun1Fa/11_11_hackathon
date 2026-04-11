"""
orchestrator.py
---------------
Integration Orchestrator — The "Bridge" between WhatsApp and the AI Backend.
"""

import os
import logging
import requests
from datetime import datetime, timezone
from adithyan_inte.supabase_client import supabase
from adithyan_inte.whatsapp import send_whatsapp_message, mark_message_read
from adithyan_inte.handoff import handle_handoff

logger = logging.getLogger(__name__)

# Teammate's AI Backend URL
AI_BACKEND_URL: str = os.getenv("AI_BACKEND_URL", "http://localhost:5001")

def process_whatsapp_message(phone_number: str, message_text: str, wa_msg_id: str) -> None:
    """
    Core integration pipeline:
    1. Check handoff status.
    2. Mark message as read.
    3. Call teammate's AI backend.
    4. Log conversation.
    5. Dispatch AI response.
    """
    
    # ── 1. Handoff Guard ────────────────────────────────────────────────
    res = supabase.table("customers").select("id, is_handoff_active").eq("phone_number", phone_number).execute()
    customer = res.data[0] if res.data else None
    
    if customer and customer.get("is_handoff_active"):
        logger.info("Handoff active for %s — logging message without AI reply.", phone_number)
        _log_conversation(phone_number, message_text, "inbound", {"skipped": "handoff_active"})
        return

    # ── 2. UI Feedback ──────────────────────────────────────────────────
    mark_message_read(wa_msg_id)

    # ── 3. Call Teammate's Brain ────────────────────────────────────────
    # Attempt to analyze and generate a reply in one or two hops
    ai_data = _call_ai_backend(phone_number, message_text)
    
    reply_text = ai_data.get("reply_text") or ai_data.get("response")
    action = ai_data.get("action", "auto_reply")
    intent = ai_data.get("intent", "general")
    
    # ── 4. Log Encounter ───────────────────────────────────────────────
    _log_conversation(phone_number, message_text, "inbound", ai_data)

    # ── 5. Action Routing ───────────────────────────────────────────────
    if action == "handoff":
        handle_handoff(phone_number, trigger_reason=f"AI Intent: {intent}")
    elif reply_text:
        send_whatsapp_message(to=phone_number, message=reply_text, reply_to_msg_id=wa_msg_id)
        # Log the outbound reply
        _log_conversation(phone_number, reply_text, "outbound", {"type": "auto_reply"})

def _call_ai_backend(phone_number: str, message_text: str) -> dict:
    """
    Communicates with the external AI backend for intelligence.
    Adjust the path (/analyze) if the teammate uses a different endpoint.
    """
    try:
        response = requests.post(
            f"{AI_BACKEND_URL}/analyze",
            json={"phone_number": phone_number, "message": message_text},
            timeout=20
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.error("Failed to reach teammate's AI backend: %s", exc)
        # Safe fallback
        return {
            "reply_text": "Thank you for reaching out! We've received your message and will get back to you soon.",
            "action": "auto_reply",
            "intent": "general"
        }

def _log_conversation(phone_number: str, text: str, direction: str, metadata: dict) -> None:
    """Logs history to Supabase."""
    try:
        supabase.table("conversations").insert({
            "phone_number": phone_number,
            "message_text": text,
            "direction": direction,
            "source": "whatsapp",
            "ai_metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception as exc:
        logger.warning("Log failed: %s", exc)
