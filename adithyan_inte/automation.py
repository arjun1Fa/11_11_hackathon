"""
automation.py
-------------
APScheduler configuration for Study Abroad automated triggers.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from adithyan_inte.supabase_client import supabase
from adithyan_inte.messaging import send_outbound_message

logger = logging.getLogger(__name__)

# Config
CART_CHECK_INTERVAL_MINUTES: int = int(os.getenv("CART_CHECK_INTERVAL_MINUTES", "2"))
CHURN_SCORE_THRESHOLD: float = float(os.getenv("CHURN_SCORE_THRESHOLD", "0.6"))

# Templates
ENQUIRY_RECOVERY_TEMPLATE: str = (
    "Hi {name}! 👋 We noticed you were exploring {country} packages.\n\n"
    "🌍 Are you still interested in starting your journey there?\n\n"
    "Reply *YES* to continue our consultation, or let us know if you have any "
    "questions about visa or admission! 🎓"
)

def enquiry_abandonment_check() -> None:
    """Checks for abandoned study abroad enquiries."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=CART_CHECK_INTERVAL_MINUTES)
    
    try:
        result = (
            supabase.table("enquiry_events")
            .select("id, customer_id, phone_number, country")
            .eq("status", "abandoned")
            .lte("updated_at", cutoff.isoformat())
            .execute()
        )
        for enq in (result.data or []):
            _process_abandoned_enquiry(enq)
    except Exception as exc:
        logger.error("Enquiry job failed: %s", exc)

def _process_abandoned_enquiry(enq: dict) -> None:
    customer_id = enq["customer_id"]
    phone_number = enq["phone_number"]
    country = enq.get("country", "your country of choice")
    
    # Simple name fetch
    res = supabase.table("customers").select("name").eq("id", customer_id).maybe_single().execute()
    name = (res.data or {}).get("name") or "there"
    
    message = ENQUIRY_RECOVERY_TEMPLATE.format(name=name, country=country)
    
    success = send_outbound_message(phone_number, message, message_type="enquiry_recovery", customer_id=customer_id)
    
    if success:
        supabase.table("enquiry_events").update({
            "status": "recovery_sent",
            "recovery_sent_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", enq["id"]).execute()

def build_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        func=enquiry_abandonment_check,
        trigger="interval",
        minutes=CART_CHECK_INTERVAL_MINUTES,
        id="enquiry_job"
    )
    return scheduler

scheduler = build_scheduler()
