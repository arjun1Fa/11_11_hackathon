"""
seed_churn.py
─────────────────────────────────────────────────────────────────
Populates realistic churn data for ALL customers in Supabase.

Strategy:
  1. Fetch every customer
  2. Assign a simulated 'last_active' date (varied across 1-45 days)
     so different customers show different risk levels
  3. Run the churn scoring formula
  4. Write churn_score back to Supabase (only columns that exist)

Run once to seed data:
  python seed_churn.py
"""

import os
import sys
import random
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from supabase_client import supabase

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ── Churn formula (mirrors churn_scorer.py but standalone) ───────────────────
def compute_local_score(days_inactive: int, abandoned_rate: float) -> dict:
    days_inactive_norm   = min(days_inactive / 30, 1.0)
    message_drop_rate    = 0.5 if days_inactive > 7 else 0.0
    score = (0.5 * days_inactive_norm) + (0.3 * abandoned_rate) + (0.2 * message_drop_rate)
    score = round(min(score, 1.0), 2)
    risk  = "high" if score > 0.7 else ("medium" if score > 0.4 else "low")
    return {"churn_score": score, "risk_level": risk}


# ── Intent pool for demo variety ─────────────────────────────────────────────
INTENTS = [
    "visa_query", "fee_payment", "document_submission",
    "university_shortlist", "scholarship_enquiry", "general",
    "application_status", "accommodation_help"
]

# ── Customer profiles for a realistic spread ──────────────────────────────────
# (days_inactive, abandoned_rate)  → expected risk
PROFILES = [
    (1,  0.0),   # very active   → low
    (3,  0.1),   # recent        → low
    (7,  0.2),   # week old      → low-medium
    (10, 0.3),   # 10 days gone  → medium
    (15, 0.4),   # 2 weeks gone  → medium
    (20, 0.5),   # 3 weeks gone  → medium-high
    (25, 0.6),   # high risk     → high
    (35, 0.8),   # very high     → high
    (45, 1.0),   # lost          → high
]


def run():
    logger.info("\n═══════════════════════════════════════════════")
    logger.info("  Smartilee — Churn Data Seeder")
    logger.info("═══════════════════════════════════════════════\n")

    # 1. Fetch all customers
    result = supabase.table("customers").select("id, phone_number").execute()
    customers = result.data or []

    if not customers:
        logger.error("❌ No customers found in the database. Add some first!")
        return

    logger.info("Found %d customers. Seeding churn data...\n", len(customers))

    succeeded = 0
    failed    = 0

    for i, customer in enumerate(customers):
        phone  = customer["phone_number"]
        cid    = customer["id"]

        # Assign a realistic profile (cycle through PROFILES for variety)
        profile         = PROFILES[i % len(PROFILES)]
        days_inactive   = profile[0] + random.randint(-1, 2)   # slight randomness
        abandoned_rate  = min(profile[1] + random.uniform(-0.05, 0.05), 1.0)
        days_inactive   = max(0, days_inactive)

        churn   = compute_local_score(days_inactive, abandoned_rate)
        score   = churn["churn_score"]
        risk    = churn["risk_level"]
        intent  = random.choice(INTENTS)
        last_active = (datetime.now(timezone.utc) - timedelta(days=days_inactive)).isoformat()

        try:
            # Write to Supabase — only use columns we KNOW exist
            supabase.table("customers").update({
                "last_active":  last_active,
                "churn_score":  score,
            }).eq("id", cid).execute()

            risk_icon = "🔴" if risk == "high" else ("🟡" if risk == "medium" else "🟢")
            logger.info(
                "%s %-18s | inactive=%2dd | churn=%.2f | %s %s | intent=%s",
                risk_icon, phone, days_inactive, score, risk.upper().ljust(6), "", intent
            )
            succeeded += 1

        except Exception as exc:
            logger.warning("⚠️  Skipped %-18s: %s", phone, exc)
            failed += 1

    logger.info(
        "\n─────────────────────────────────────────────────\n"
        "  ✅ Updated: %d  |  ⚠️  Skipped: %d\n"
        "─────────────────────────────────────────────────\n",
        succeeded, failed
    )
    logger.info("Your frontend will now show real churn risk levels!\n")


if __name__ == "__main__":
    run()
