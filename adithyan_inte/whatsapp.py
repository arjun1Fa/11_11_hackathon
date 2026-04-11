"""
whatsapp.py
-----------
WhatsApp Business Cloud API integration for Smartilee.

Handles:
  1. Webhook verification (GET /webhook) — Meta's handshake
  2. Inbound message parsing  — extracts phone + text from Meta's payload
  3. Outbound message sending — sends text replies via the Graph API

Meta API reference:
  https://developers.facebook.com/docs/whatsapp/cloud-api

Environment variables needed (add to .env):
  WHATSAPP_VERIFY_TOKEN     — any string you set in the Meta App dashboard
  WHATSAPP_ACCESS_TOKEN     — permanent system user token from Meta
  WHATSAPP_PHONE_NUMBER_ID  — the Phone Number ID (NOT the number itself)
  WHATSAPP_API_VERSION      — default: v19.0
"""

import os
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
VERIFY_TOKEN: str       = os.getenv("WHATSAPP_VERIFY_TOKEN", "smartilee_verify_token")
ACCESS_TOKEN: str       = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
PHONE_NUMBER_ID: str    = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
API_VERSION: str        = os.getenv("WHATSAPP_API_VERSION", "v19.0")

GRAPH_API_BASE: str     = f"https://graph.facebook.com/{API_VERSION}"


# ═══════════════════════════════════════════════════════════════════════════════
# Webhook verification (GET /webhook)
# ═══════════════════════════════════════════════════════════════════════════════

def verify_webhook(args: dict) -> tuple[str | None, int]:
    """
    Handles the one-time webhook verification handshake from Meta.

    Meta sends:
      hub.mode          = "subscribe"
      hub.verify_token  = <your VERIFY_TOKEN>
      hub.challenge     = <random string to echo back>

    Returns:
        (challenge_string, 200)  on success
        (None, 403)              if token mismatch
    """
    mode      = args.get("hub.mode")
    token     = args.get("hub.verify_token")
    challenge = args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully.")
        return challenge, 200

    logger.warning(
        "Webhook verification FAILED — received token '%s', expected '%s'.",
        token, VERIFY_TOKEN,
    )
    return None, 403


# ═══════════════════════════════════════════════════════════════════════════════
# Inbound payload parser (POST /webhook)
# ═══════════════════════════════════════════════════════════════════════════════

def parse_inbound_message(payload: dict) -> list[dict]:
    """
    Parses Meta's webhook payload and extracts all inbound text messages.

    Meta wraps everything in a nested structure:
      payload.entry[].changes[].value.messages[]

    Returns:
        List of dicts:
        [
          {
            "phone_number": "+919876543210",
            "message_text": "Hello!",
            "whatsapp_msg_id": "wamid.xxx",
            "display_phone_number": "91XXXXXXXXXX",
            "contact_name": "Rajesh Kumar",
          },
          ...
        ]
        Returns [] if payload is a status update (delivered/read) or has
        no text messages.
    """
    messages = []

    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # Ignore status update webhooks (sent / delivered / read)
                if "statuses" in value and "messages" not in value:
                    logger.debug("Received status update webhook — skipping.")
                    continue

                raw_messages = value.get("messages", [])
                contacts     = value.get("contacts", [])

                for msg in raw_messages:
                    # Only process text messages for now
                    if msg.get("type") != "text":
                        logger.info(
                            "Non-text message type '%s' received — skipping.",
                            msg.get("type"),
                        )
                        continue

                    phone_number   = msg.get("from", "")   # E.164 format
                    whatsapp_msg_id= msg.get("id", "")
                    text_body      = msg.get("text", {}).get("body", "")

                    # Extract display name from contacts array
                    contact_name = ""
                    if contacts:
                        profile = contacts[0].get("profile", {})
                        contact_name = profile.get("name", "")

                    # Get the WhatsApp number the customer messaged
                    display_phone = value.get("metadata", {}).get(
                        "display_phone_number", ""
                    )

                    if phone_number and text_body:
                        messages.append(
                            {
                                "phone_number":        f"+{phone_number}",
                                "message_text":        text_body,
                                "whatsapp_msg_id":     whatsapp_msg_id,
                                "display_phone_number": display_phone,
                                "contact_name":        contact_name,
                            }
                        )

    except Exception as exc:
        logger.error("Error parsing WhatsApp payload: %s", exc)

    return messages


# ═══════════════════════════════════════════════════════════════════════════════
# Send reply via WhatsApp Cloud API
# ═══════════════════════════════════════════════════════════════════════════════

def send_whatsapp_message(
    to: str,
    message: str,
    reply_to_msg_id: Optional[str] = None,
) -> bool:
    """
    Sends a text message via the WhatsApp Business Cloud API.

    Args:
        to:               Recipient in E.164 format (e.g. "+919876543210")
        message:          Plain text body (supports WhatsApp markdown: *bold*, _italic_)
        reply_to_msg_id:  Optional — quote the original inbound message

    Returns:
        True on success, False on failure.
    """
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        logger.error(
            "WhatsApp not configured — set WHATSAPP_ACCESS_TOKEN and "
            "WHATSAPP_PHONE_NUMBER_ID in .env"
        )
        return False

    # Remove leading '+' — Graph API expects plain E.164 digits
    recipient = to.lstrip("+")

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type":    "individual",
        "to":                recipient,
        "type":              "text",
        "text": {
            "preview_url": False,
            "body":        message,
        },
    }

    # Optionally quote the message we're replying to
    if reply_to_msg_id:
        payload["context"] = {"message_id": reply_to_msg_id}

    url = f"{GRAPH_API_BASE}/{PHONE_NUMBER_ID}/messages"

    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type":  "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()
        resp_json = response.json()
        wa_msg_id = (
            resp_json.get("messages", [{}])[0].get("id", "unknown")
        )
        logger.info(
            "WhatsApp message sent — to=%s | wa_msg_id=%s", to, wa_msg_id
        )
        return True

    except requests.HTTPError as exc:
        logger.error(
            "WhatsApp API HTTP error — status=%s | body=%s",
            exc.response.status_code,
            exc.response.text,
        )
    except requests.RequestException as exc:
        logger.error("WhatsApp API request failed: %s", exc)

    return False


# ═══════════════════════════════════════════════════════════════════════════════
# Mark message as read (optional — shows blue ticks)
# ═══════════════════════════════════════════════════════════════════════════════

def mark_message_read(whatsapp_msg_id: str) -> None:
    """
    Sends a read receipt for the inbound message.
    This shows the double blue ✓✓ ticks on the customer's phone.
    """
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        return

    url = f"{GRAPH_API_BASE}/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "status":            "read",
        "message_id":        whatsapp_msg_id,
    }

    try:
        requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            timeout=5,
        )
    except Exception as exc:
        logger.warning("Failed to mark message as read: %s", exc)
