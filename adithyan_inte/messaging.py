"""
messaging.py
------------
Internal messaging abstraction for Smartilee Standalone.
Removed Happilee and WhatsApp integration as per latest request.
"""

import os
import logging
from datetime import datetime, timezone
from supabase_client import supabase

logger = logging.getLogger(__name__)

def send_outbound_message(
    recipient: str,
    message: str,
    message_type: str = "auto_reply",
    customer_id: str | None = None,
) -> bool:
    """
    Sends an outbound message to the recipient and logs to Supabase.
    """
    success = False
    try:
        # 1. Dispatch via WhatsApp Direct
        from whatsapp import send_whatsapp_message
        success = send_whatsapp_message(to=recipient, message=message)
        
        # 2. Log to Console
        logger.info("[OUTBOUND] To=%s | Type=%s | Success=%s", recipient, message_type, success)
        
        # 3. Persist to Supabase
        supabase.table("conversations").insert({
            "customer_id": customer_id,
            "phone_number": recipient,
            "message_text": message,
            "direction": "outbound",
            "source": "whatsapp",
            "message_type": message_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        return success
    except Exception as exc:
        logger.error("Failed to send/log outbound message: %s", exc)
        return False
