"""
messaging.py
------------
Outbound messaging abstraction layer.

Supports three backends (set via MESSAGING_BACKEND in .env):

  "log"      — Prints to console + logs to DB (default / dev)
  "whatsapp" — Sends via WhatsApp Business Cloud API (whatsapp.py)
  "happilee" — Sends via Happilee gateway (legacy option)

Changing backends requires only one .env change — no code edits.
"""

import os
import logging
from datetime import datetime, timezone

from supabase_client import supabase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configurable constants — override via environment variables
# ---------------------------------------------------------------------------
HAPPILEE_API_URL: str = os.getenv("HAPPILEE_API_URL", "")
HAPPILEE_API_TOKEN: str = os.getenv("HAPPILEE_API_TOKEN", "")
MESSAGING_BACKEND: str = os.getenv("MESSAGING_BACKEND", "log")  # "log" | "whatsapp" | "happilee"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_outbound_message(
    recipient: str,
    message: str,
    message_type: str = "auto_reply",
    customer_id: str | None = None,
) -> bool:
    """
    Sends (or stubs) an outbound message to the given recipient.

    Args:
        recipient:    Destination phone number / identifier.
        message:      The plain text content to send.
        message_type: Classification tag stored in the DB
                      (e.g. "auto_reply", "upsell", "escalation_alert").
        customer_id:  Optional customer UUID for DB logging.

    Returns:
        True if the send succeeded, False otherwise.
    """
    success = False

    if MESSAGING_BACKEND == "whatsapp":
        from whatsapp import send_whatsapp_message  # lazy import
        success = send_whatsapp_message(
            to=recipient,
            message=message,
            reply_to_msg_id=None,
        )

    elif MESSAGING_BACKEND == "happilee" and HAPPILEE_API_URL:
        success = _send_via_happilee(recipient, message)

    else:
        # ── Log stub: used in dev / when no channel is configured ──
        logger.info(
            "[OUTBOUND MSG] To=%s | Type=%s | Body=%s", recipient, message_type, message
        )
        print(
            f"\n📤 OUTBOUND MESSAGE\n"
            f"   To      : {recipient}\n"
            f"   Type    : {message_type}\n"
            f"   Message : {message}\n"
        )
        success = True  # stub always succeeds

    # Persist outbound message to DB regardless of channel
    _log_outbound_to_db(
        recipient=recipient,
        message=message,
        message_type=message_type,
        customer_id=customer_id,
        delivered=success,
    )

    return success


# ---------------------------------------------------------------------------
# Channel implementations
# ---------------------------------------------------------------------------

def _send_via_happilee(recipient: str, message: str) -> bool:
    """
    Sends a message via the Happilee WhatsApp gateway.
    Swap this implementation once API credentials are available.
    """
    import requests  # lazy import — only needed when Happilee is active

    try:
        response = requests.post(
            f"{HAPPILEE_API_URL}/sendMessage",
            json={"to": recipient, "message": message},
            headers={"Authorization": f"Bearer {HAPPILEE_API_TOKEN}"},
            timeout=10,
        )
        response.raise_for_status()
        logger.info("Happilee send OK — to=%s", recipient)
        return True
    except requests.RequestException as exc:
        logger.error("Happilee send FAILED — to=%s | error=%s", recipient, exc)
        return False


# ---------------------------------------------------------------------------
# Database logging
# ---------------------------------------------------------------------------

def _log_outbound_to_db(
    recipient: str,
    message: str,
    message_type: str,
    customer_id: str | None,
    delivered: bool,
) -> None:
    """Persists the outbound message record to `conversations`."""
    try:
        supabase.table("conversations").insert(
            {
                "phone_number": recipient,
                "customer_id": customer_id,
                "direction": "outbound",
                "message_text": message,
                "message_type": message_type,
                "delivered": delivered,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
    except Exception as exc:
        logger.warning("Could not log outbound message to DB: %s", exc)
