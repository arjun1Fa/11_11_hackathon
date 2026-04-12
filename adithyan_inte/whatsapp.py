"""
whatsapp.py
-----------
Direct Meta WhatsApp Business Cloud API integration.
Manages webhook payloads and outbound Graph API requests.
"""

import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Configuration (Meta)
WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_VERSION: str = os.getenv("WHATSAPP_API_VERSION", "v19.0")
WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

# ── Webhook Verification (GET) ────────────────────────────────────────────────

def verify_webhook(mode: str, token: str, challenge: str) -> Optional[str]:
    """
    Verifies the Meta webhook challenge token.
    Returns the challenge string if valid, else None.
    """
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verification SUCCESS.")
        return challenge
    
    logger.warning("Webhook verification FAILED. Mode: %s, Token: %s", mode, token)
    return None

# ── Message Parsing (POST) ────────────────────────────────────────────────────

def parse_inbound_message(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parses a raw Meta webhook payload to extract core message data.
    
    Returns:
        { "phone_number": str, "message_text": str, "wa_msg_id": str } or None
    """
    try:
        # Navigate the complex Meta JSON structure
        # entry[] -> changes[] -> value -> messages[]
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        if "messages" not in value:
            # Could be a status update (delivered/read), ignore for now
            return None
            
        message = value["messages"][0]
        phone_number = message["from"]
        
        # Extract text content
        msg_type = message.get("type")
        message_text = ""
        
        if msg_type == "text":
            message_text = message.get("text", {}).get("body", "")
        elif msg_type == "button":
            message_text = message.get("button", {}).get("text", "")
        elif msg_type == "interactive":
            # Handle list_reply or button_reply
            inter = message.get("interactive", {})
            if inter.get("type") == "button_reply":
                message_text = inter.get("button_reply", {}).get("title", "")
            elif inter.get("type") == "list_reply":
                message_text = inter.get("list_reply", {}).get("title", "")
                
        if not message_text:
            return None
            
        return {
            "phone_number": phone_number,
            "message_text": message_text,
            "wa_msg_id": message["id"],
        }
        
    except (IndexError, KeyError, TypeError) as exc:
        logger.debug("Non-message payload received or parsing error: %s", exc)
        return None

# ── Outbound Messaging ───────────────────────────────────────────────────────

def send_whatsapp_message(
    to: str,
    message: str,
    reply_to_msg_id: Optional[str] = None
) -> bool:
    """
    Sends a text message via Meta Graph API.
    """
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("WhatsApp credentials missing in environment.")
        return False

    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
    
    payload: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }
    
    if reply_to_msg_id:
        payload["context"] = {"message_id": reply_to_msg_id}
        
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("WhatsApp send successful — to=%s", to)
        return True
    except requests.RequestException as exc:
        logger.error("WhatsApp send FAILED — to=%s | error=%s", to, exc)
        return False

def mark_message_read(wa_msg_id: str) -> None:
    """Marks an incoming message as read in the student's WhatsApp app."""
    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
    
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": wa_msg_id
    }
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception:
        pass
