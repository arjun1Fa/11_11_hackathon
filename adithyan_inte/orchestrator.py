"""
orchestrator.py
---------------
Integration Orchestrator — The "Bridge" between WhatsApp and the AI Backend.
"""

import os
import logging
import requests
from datetime import datetime, timezone
from supabase_client import supabase
from whatsapp import send_whatsapp_message, mark_message_read
from handoff import handle_handoff
from churn_scorer import compute_churn_score

logger = logging.getLogger(__name__)

# Teammate's AI Backend URL
AI_BACKEND_URL: str = os.getenv("AI_BACKEND_URL", "http://localhost:5001")

# Simulator Mode — routes replies back to the local simulator UI instead of WhatsApp
SIMULATOR_MODE: bool = os.getenv("SIMULATOR_MODE", "false").lower() == "true"
SIMULATOR_REPLY_URL: str = os.getenv("SIMULATOR_REPLY_URL", "http://localhost:5050/receive")

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
    
    # ── 4. Update Customer Profile in Supabase ─────────────────────────
    _update_customer_profile(phone_number, intent, action)

    # ── 5. Log Encounter ────────────────────────────────────────────────
    _log_conversation(phone_number, message_text, "inbound", ai_data)

    # ── 5. Action Routing ───────────────────────────────────────────────
    if action == "handoff":
        handle_handoff(phone_number, trigger_reason=f"AI Intent: {intent}")
    elif action == "start_call":
        if SIMULATOR_MODE:
            try:
                import requests as _req
                _req.post(SIMULATOR_REPLY_URL, json={
                    "text": reply_text or "Connecting you to a voice counsellor...",
                    "metadata": {"intent": intent, "action": "start_call"}
                }, timeout=5)
                logger.info("[SIM MODE] Call triggered in simulator UI")
            except Exception as e:
                logger.warning("[SIM MODE] Could not reach simulator for call: %s", e)
        else:
            # Fallback for real WhatsApp: send a text alerting them of the call
            send_whatsapp_message(to=phone_number, message="Connecting you to a voice counsellor. You will receive a call momentarily.", reply_to_msg_id=wa_msg_id)
        
        _log_conversation(phone_number, "CALL TRIGGERED", "outbound", {"type": "call_start"})

    elif reply_text:
        if SIMULATOR_MODE:
            try:
                import requests as _req
                _req.post(SIMULATOR_REPLY_URL, json={
                    "text": reply_text,
                    "metadata": {"intent": intent, "action": action}
                }, timeout=5)
                logger.info("[SIM MODE] Reply sent to simulator UI")
            except Exception as e:
                logger.warning("[SIM MODE] Could not reach simulator: %s", e)
        else:
            send_whatsapp_message(to=phone_number, message=reply_text, reply_to_msg_id=wa_msg_id)
        _log_conversation(phone_number, reply_text, "outbound", {"type": "auto_reply"})

def _get_conversation_history(phone_number: str, limit: int = 10) -> list:
    """Fetches the last N messages from Supabase to provide context to the AI."""
    try:
        res = supabase.table("conversations") \
            .select("message_text, direction") \
            .eq("phone_number", phone_number) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        # Format for AI: role (user/assistant) and content
        history = []
        for msg in reversed(res.data or []):
            history.append({
                "role": "user" if msg["direction"] == "inbound" else "assistant",
                "content": msg["message_text"]
            })
        
        logger.info("[AI] Successfully fetched %d messages of history for %s", len(history), phone_number)
        return history
    except Exception as e:
        logger.warning(f"[AI] Failed to fetch history for {phone_number}: {e}")
        return []

def _call_ai_backend(phone_number: str, message_text: str) -> dict:
    """
    Communicates with the teammate's AI backend.
    Sends history + current message for better context (memory).
    """
    base_url = AI_BACKEND_URL.rstrip("/")
    history = _get_conversation_history(phone_number)
    
    # ── STEP 1: Analyze Intent and Action ────────────────────────────
    try:
        logger.info("[AI] Calling /analyze for %s (context size: %d turns)...", phone_number, len(history))
        response = requests.post(
            f"{base_url}/analyze",
            json={
                "phone_number": phone_number,
                "message_text": message_text,
                "messages": history,   # Renamed from 'history' to 'messages'
                "chat_history": history # Also sending this just in case
            },
            timeout=60
        )
        response.raise_for_status()
        ai_data = response.json()
        
        action = ai_data.get("action", "auto_reply")
        intent = ai_data.get("intent", "general")
        logger.info("[AI] Action: %s | Intent: %s", action, intent)

        # ── STEP 2: Generate Reply Text (only if needed) ─────────────
        if action in ["auto_reply", "start_call", "onboarding"]:
            logger.info("[AI] Calling /generate-reply...")
            gen_resp = requests.post(
                f"{base_url}/generate-reply",
                json={
                    "phone_number": phone_number,
                    "message_text": message_text,
                    "messages": history,
                    "chat_history": history
                },
                timeout=60
            )
            gen_resp.raise_for_status()
            gen_data = gen_resp.json()
            
            # Merge the generated text into our data
            ai_data["reply_text"] = gen_data.get("reply_text") or gen_data.get("response")
            logger.info("[AI] Reply generated: %s...", ai_data["reply_text"][:30])
        
        return ai_data

    except Exception as exc:
        logger.error("[AI] Orchestration error: %s", exc)
        # Safe fallback based on the error type
        return {
            "reply_text": f"Sorry, I had trouble reaching the AI. (Error: {str(exc)[:50]}...)",
            "action": "auto_reply",
            "intent": "error_fallback"
        }

def _update_customer_profile(phone_number: str, intent: str, action: str) -> None:
    """
    After every conversation, update the customer's profile in Supabase:
    - last_active  → set to NOW (marks them as recently engaged)
    - churn_score  → recomputed using the weighted formula
    - risk_level   → low / medium / high
    - last_intent  → stores what the AI understood they wanted
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        
        # Step 1: Mark as active right now
        supabase.table("customers").update({
            "last_active": now
        }).eq("phone_number", phone_number).execute()
        
        # Step 2: Recompute churn score
        churn_data = compute_churn_score(phone_number)
        churn_score = churn_data.get("churn_score", 0.0)
        risk_level  = churn_data.get("risk_level", "low")
        
        # Step 3: Write everything back
        supabase.table("customers").update({
            "churn_score": churn_score,
            "risk_level":  risk_level,
            "last_intent": intent,
        }).eq("phone_number", phone_number).execute()
        
        logger.info(
            "[PROFILE] %s → active=%s | churn=%.2f (%s) | intent=%s",
            phone_number, now[:19], churn_score, risk_level, intent
        )
    except Exception as exc:
        logger.warning("[PROFILE] Update skipped (schema or DB issue): %s", exc)


def _log_conversation(phone_number: str, text: str, direction: str, metadata: dict) -> None:
    """Logs history to Supabase — uses only the most basic columns to avoid schema errors."""
    try:
        supabase.table("conversations").insert({
            "phone_number": phone_number,
            "message_text": text,
            "direction": direction
        }).execute()
    except Exception:
        # Silently fail logging if DB is not ready
        pass


# ── Telegram Pipeline ─────────────────────────────────────────────────────────

def process_telegram_message(
    chat_id: str,
    message_text: str,
    telegram_msg_id: str
) -> None:
    """
    Telegram integration pipeline — mirrors process_whatsapp_message.
    Uses chat_id as the unique user identifier instead of phone_number.

    Flow:
      1. Guard against handoff-active users
      2. Show typing indicator
      3. Call AI backend
      4. Log + dispatch reply
    """
    from telegram_bot import send_telegram_message, send_typing_action

    logger.info("[TELEGRAM] Incoming from chat_id=%s | text=%s", chat_id, message_text[:50])

    # ── 1. Handoff Guard ─────────────────────────────────────────────────
    res = supabase.table("customers").select("id, is_handoff_active").eq("phone_number", str(chat_id)).execute()
    customer = res.data[0] if res.data else None

    if customer and customer.get("is_handoff_active"):
        logger.info("[TELEGRAM] Handoff active for %s — skipping AI reply.", chat_id)
        _log_conversation(str(chat_id), message_text, "inbound", {"skipped": "handoff_active"})
        send_telegram_message(
            chat_id=chat_id,
            message="⏳ A human agent is already handling your case. They'll respond shortly.",
            reply_to_msg_id=telegram_msg_id,
        )
        return

    # ── 4. Typing indicator ──────────────────────────────────────────────
    send_typing_action(chat_id)

    # ── 5. Call Teammate's AI Backend ────────────────────────────────────
    ai_data    = _call_ai_backend(phone_number=chat_id, message_text=message_text)
    reply_text = ai_data.get("reply_text") or ai_data.get("response")
    action     = ai_data.get("action", "auto_reply")
    intent     = ai_data.get("intent", "general")

    logger.info("[TELEGRAM] Action=%s | Intent=%s", action, intent)

    # ── 6. Log inbound message to Supabase ───────────────────────────────
    _log_conversation(chat_id, message_text, "inbound", ai_data)

    # ── 7. Dispatch AI reply ──────────────────────────────────────────────
    if action == "handoff":
        send_telegram_message(
            chat_id=chat_id,
            message="🙋 Connecting you to a human agent now. Please wait a moment!",
            reply_to_msg_id=telegram_msg_id,
        )
        _log_conversation(chat_id, "HANDOFF TRIGGERED", "outbound", {"type": "handoff"})

    elif action == "start_call":
        send_telegram_message(
            chat_id=chat_id,
            message="📞 A voice counsellor will reach out to you shortly!",
            reply_to_msg_id=telegram_msg_id,
        )
        _log_conversation(chat_id, "CALL TRIGGERED", "outbound", {"type": "call_start"})

    elif reply_text:
        success = send_telegram_message(
            chat_id=chat_id,
            message=reply_text,
            reply_to_msg_id=telegram_msg_id,
        )
        if success:
            _log_conversation(chat_id, reply_text, "outbound", {"type": "auto_reply"})

    else:
        logger.warning("[TELEGRAM] No reply_text from AI — sending fallback.")
        send_telegram_message(
            chat_id=chat_id,
            message="Sorry, I'm having trouble right now. Please try again in a moment.",
            reply_to_msg_id=telegram_msg_id,
        )

