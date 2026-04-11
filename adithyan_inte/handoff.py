"""
handoff.py
----------
Manages the human-handoff lifecycle for Smartilee.

When the AI determines a conversation needs a human agent it:
  1. Inserts a record into `handoff_queue` with status='pending'.
  2. Flips `is_handoff_active = True` on the customer row so AI
     replies are blocked for that customer.
  3. Prepares an "Escalation Alert" payload (sent to the outbound
     notifier — currently a stub that can be swapped for Happilee).

Design note: the `send_outbound_message` call at the bottom is
deliberately isolated so it can be replaced by a single-line change
when the WhatsApp / Happilee integration is ready.
"""

import os
import logging
from datetime import datetime, timezone

from supabase_client import supabase
from messaging import send_outbound_message  # swap here for Happilee later

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def handle_handoff(phone_number: str, trigger_reason: str = "AI escalation") -> dict:
    """
    Executes the full handoff sequence for a customer.

    Args:
        phone_number: The customer's phone number (used as their unique key).
        trigger_reason: A brief description of why the handoff was triggered.

    Returns:
        dict with `success` (bool) and `handoff_id` (str | None).
    """
    customer = _get_customer(phone_number)
    if customer is None:
        logger.error("Handoff triggered but customer not found: %s", phone_number)
        return {"success": False, "handoff_id": None, "error": "Customer not found"}

    customer_id = customer["id"]
    customer_name = customer.get("name", phone_number)

    # Step 1 — Insert into the handoff queue
    handoff_id = _create_handoff_record(customer_id, phone_number, trigger_reason)
    if handoff_id is None:
        return {"success": False, "handoff_id": None, "error": "DB insert failed"}

    # Step 2 — Block further AI replies for this customer
    _set_handoff_active(customer_id, active=True)

    # Step 3 — Send escalation alert (outbound stub)
    _send_escalation_alert(
        phone_number=phone_number,
        customer_name=customer_name,
        trigger_reason=trigger_reason,
        handoff_id=handoff_id,
    )

    logger.info(
        "Handoff initiated — customer: %s | handoff_id: %s | reason: %s",
        phone_number, handoff_id, trigger_reason,
    )
    return {"success": True, "handoff_id": handoff_id}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_customer(phone_number: str) -> dict | None:
    """Fetches the customer record by phone number."""
    try:
        result = (
            supabase.table("customers")
            .select("id, name, is_handoff_active")
            .eq("phone_number", phone_number)
            .single()
            .execute()
        )
        return result.data
    except Exception as exc:
        logger.error("Error fetching customer %s: %s", phone_number, exc)
        return None


def _create_handoff_record(
    customer_id: str, phone_number: str, reason: str
) -> str | None:
    """
    Inserts a row into `handoff_queue`.

    Returns the new row's UUID on success, None on failure.
    """
    payload = {
        "customer_id": customer_id,
        "phone_number": phone_number,
        "status": "pending",
        "trigger_reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        result = supabase.table("handoff_queue").insert(payload).execute()
        return result.data[0]["id"]
    except Exception as exc:
        logger.error("Failed to insert handoff record: %s", exc)
        return None


def _set_handoff_active(customer_id: str, active: bool) -> None:
    """Sets the `is_handoff_active` flag on the customers table."""
    try:
        supabase.table("customers").update(
            {"is_handoff_active": active}
        ).eq("id", customer_id).execute()
    except Exception as exc:
        logger.error("Failed to update handoff flag for %s: %s", customer_id, exc)


def _send_escalation_alert(
    phone_number: str, customer_name: str, trigger_reason: str, handoff_id: str
) -> None:
    """
    Composes and dispatches the escalation alert to the system owner.

    Currently routed through `messaging.send_outbound_message`.
    Replace that function's body with `happilee.send_message(...)` when ready.
    """
    alert_text = (
        f"🚨 *ESCALATION ALERT* 🚨\n\n"
        f"Customer: *{customer_name}* ({phone_number})\n"
        f"Reason: {trigger_reason}\n"
        f"Handoff ID: `{handoff_id}`\n"
        f"Status: PENDING — awaiting human agent\n\n"
        f"Please respond in the Smartilee dashboard or WhatsApp directly."
    )

    # Notify the system owner (phone number pulled from env)
    admin_phone = os.getenv("WHATSAPP_ADMIN_PHONE", phone_number)
    send_outbound_message(
        recipient=admin_phone,
        message=alert_text,
        message_type="escalation_alert",
    )
