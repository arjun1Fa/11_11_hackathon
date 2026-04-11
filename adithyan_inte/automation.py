"""
automation.py
-------------
APScheduler configuration for Smartilee's automated trigger system.

Two background jobs are registered:

  1. cart_abandonment_check  — runs every 2 minutes (demo) / 30 minutes (prod)
     Detects abandoned carts and fires a recovery message.

  2. daily_churn_reengagement — runs once per day at 09:00
     Identifies at-risk customers (high churn_score) and prepares
     re-engagement notifications.

Usage:
    from automation import scheduler
    scheduler.start()   # called inside app.py at startup
"""

import os
import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from adithyan_inte.supabase_client import supabase
from adithyan_inte.messaging import send_outbound_message

logger = logging.getLogger(__name__)

# ── Tuneable thresholds ──────────────────────────────────────────────────────
# Switch to 30 for production; keep 2 for hackathon demo
CART_CHECK_INTERVAL_MINUTES: int = int(os.getenv("CART_CHECK_INTERVAL_MINUTES", "2"))
CART_ABANDON_THRESHOLD_MINUTES: int = int(
    os.getenv("CART_ABANDON_THRESHOLD_MINUTES", "2")
)  # 30 for prod
CHURN_SCORE_THRESHOLD: float = float(os.getenv("CHURN_SCORE_THRESHOLD", "0.6"))
DAILY_REENGAGEMENT_HOUR: int = int(os.getenv("DAILY_REENGAGEMENT_HOUR", "9"))

# ── Recovery message template (swap locale / language as needed) ─────────────
CART_RECOVERY_TEMPLATE: str = (
    "Hi {name}! 👋 We noticed you left something in your cart.\n\n"
    "🛒 *{product_name}* is still waiting for you!\n\n"
    "Ready to complete your order? Reply *YES* and we'll pick up right where you left off. "
    "Or let us know if you have any questions — we're happy to help! 😊"
)

CHURN_REENGAGEMENT_TEMPLATE: str = (
    "Hi {name}! 🌟 We miss you!\n\n"
    "It's been a while since we last connected, and we wanted to reach out with something "
    "special just for you.\n\n"
    "✨ Reply *OFFERS* to see our latest deals, or *HELP* if there's anything we can assist "
    "you with. We're always here for you! 💬"
)


# ═══════════════════════════════════════════════════════════════════════════
# Job: Cart Abandonment Recovery
# ═══════════════════════════════════════════════════════════════════════════

def cart_abandonment_check() -> None:
    """
    Finds carts with status='abandoned' that haven't been acted on,
    sends a recovery message, and marks them as 'recovery_sent'.

    Threshold: any cart abandoned more than CART_ABANDON_THRESHOLD_MINUTES ago.
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(
        minutes=CART_ABANDON_THRESHOLD_MINUTES
    )

    logger.info(
        "[Cart Job] Checking for abandoned carts older than %d min (cutoff=%s).",
        CART_ABANDON_THRESHOLD_MINUTES,
        cutoff_time.isoformat(),
    )

    try:
        result = (
            supabase.table("cart_events")
            .select("id, customer_id, phone_number, product_name, abandoned_at")
            .eq("status", "abandoned")
            .lte("abandoned_at", cutoff_time.isoformat())
            .execute()
        )
    except Exception as exc:
        logger.error("[Cart Job] Supabase query failed: %s", exc)
        return

    abandoned_carts = result.data or []
    logger.info("[Cart Job] Found %d abandoned carts.", len(abandoned_carts))

    for cart in abandoned_carts:
        _process_abandoned_cart(cart)


def _process_abandoned_cart(cart: dict) -> None:
    """Sends recovery message for a single abandoned cart."""
    cart_id = cart.get("id")
    phone_number = cart.get("phone_number")
    customer_id = cart.get("customer_id")
    product_name = cart.get("product_name", "your selected item")

    # Fetch customer name for personalisation
    customer_name = _get_customer_name(customer_id, phone_number)

    message = CART_RECOVERY_TEMPLATE.format(
        name=customer_name,
        product_name=product_name,
    )

    success = send_outbound_message(
        recipient=phone_number,
        message=message,
        message_type="cart_recovery",
        customer_id=customer_id,
    )

    if success:
        # Mark cart as recovery_sent so we don't spam the customer
        try:
            supabase.table("cart_events").update(
                {
                    "status": "recovery_sent",
                    "recovery_sent_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("id", cart_id).execute()
            logger.info("[Cart Job] Recovery sent & cart updated — cart_id=%s", cart_id)
        except Exception as exc:
            logger.error(
                "[Cart Job] Failed to update cart status for %s: %s", cart_id, exc
            )


# ═══════════════════════════════════════════════════════════════════════════
# Job: Daily Churn Re-engagement
# ═══════════════════════════════════════════════════════════════════════════

def daily_churn_reengagement() -> None:
    """
    Nightly cron — finds customers with churn_score >= CHURN_SCORE_THRESHOLD
    and sends a personalised re-engagement message.

    Only targets customers who:
    - Are NOT in an active handoff
    - Have not received a re-engagement message in the last 7 days
    """
    seven_days_ago = (
        datetime.now(timezone.utc) - timedelta(days=7)
    ).isoformat()

    logger.info(
        "[Churn Job] Running daily re-engagement sweep (threshold=%.2f).",
        CHURN_SCORE_THRESHOLD,
    )

    try:
        result = (
            supabase.table("customers")
            .select("id, name, phone_number, churn_score, last_reengagement_at")
            .gte("churn_score", CHURN_SCORE_THRESHOLD)
            .eq("is_handoff_active", False)
            .execute()
        )
    except Exception as exc:
        logger.error("[Churn Job] Supabase query failed: %s", exc)
        return

    at_risk = result.data or []
    logger.info("[Churn Job] %d at-risk customers found.", len(at_risk))

    for customer in at_risk:
        last_re = customer.get("last_reengagement_at")

        # Skip if already re-engaged within 7 days
        if last_re and last_re > seven_days_ago:
            logger.debug(
                "[Churn Job] Skipping %s — re-engaged recently.",
                customer.get("phone_number"),
            )
            continue

        _send_churn_reengagement(customer)


def _send_churn_reengagement(customer: dict) -> None:
    """Sends re-engagement message to one at-risk customer."""
    phone_number = customer.get("phone_number")
    customer_name = customer.get("name") or phone_number
    customer_id = customer.get("id")

    message = CHURN_REENGAGEMENT_TEMPLATE.format(name=customer_name)

    success = send_outbound_message(
        recipient=phone_number,
        message=message,
        message_type="churn_reengagement",
        customer_id=customer_id,
    )

    if success:
        try:
            supabase.table("customers").update(
                {"last_reengagement_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", customer_id).execute()
            logger.info(
                "[Churn Job] Re-engagement sent to %s (score=%.2f).",
                phone_number,
                customer.get("churn_score", 0),
            )
        except Exception as exc:
            logger.error(
                "[Churn Job] Failed to update last_reengagement_at for %s: %s",
                customer_id,
                exc,
            )


# ═══════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════

def _get_customer_name(customer_id: str | None, phone_number: str) -> str:
    """Fetches the customer's display name for message personalisation."""
    if not customer_id:
        return phone_number
    try:
        result = (
            supabase.table("customers")
            .select("name")
            .eq("id", customer_id)
            .maybe_single()
            .execute()
        )
        return (result.data or {}).get("name") or phone_number
    except Exception:
        return phone_number


# ═══════════════════════════════════════════════════════════════════════════
# Scheduler factory
# ═══════════════════════════════════════════════════════════════════════════

def build_scheduler() -> BackgroundScheduler:
    """
    Creates and configures the APScheduler BackgroundScheduler.
    Call `scheduler.start()` in app.py after building the Flask app.
    """
    scheduler = BackgroundScheduler(timezone="UTC")

    # ── Job 1: Cart abandonment check ────────────────────────────────────
    scheduler.add_job(
        func=cart_abandonment_check,
        trigger=IntervalTrigger(minutes=CART_CHECK_INTERVAL_MINUTES),
        id="cart_abandonment_check",
        name="Cart Abandonment Recovery",
        replace_existing=True,
        max_instances=1,  # prevent overlap
    )

    # ── Job 2: Daily churn re-engagement ─────────────────────────────────
    scheduler.add_job(
        func=daily_churn_reengagement,
        trigger=CronTrigger(hour=DAILY_REENGAGEMENT_HOUR, minute=0),
        id="daily_churn_reengagement",
        name="Daily Churn Re-engagement",
        replace_existing=True,
        max_instances=1,
    )

    logger.info(
        "Scheduler configured — cart interval: %d min | churn job: daily at %02d:00 UTC.",
        CART_CHECK_INTERVAL_MINUTES,
        DAILY_REENGAGEMENT_HOUR,
    )

    return scheduler


# Module-level singleton — imported by app.py
scheduler: BackgroundScheduler = build_scheduler()
