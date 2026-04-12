"""
churn_scorer.py
Computes a churn risk score for any student based on three behavioural signals:
 - Days since last active (50% weight)
 - Abandoned enquiry rate (30% weight)
 - Message drop rate over last 7 days vs prior 7 days (20% weight)

Score range: 0.0 (fully healthy) → 1.0 (maximum churn risk)
Thresholds: > 0.7 = high risk | 0.4–0.7 = medium | < 0.4 = healthy
"""

import sys
from datetime import datetime, timezone
from supabase import Client


# ── Risk level thresholds ─────────────────────────────────────────────────────

HIGH_RISK_THRESHOLD   = 0.7
MEDIUM_RISK_THRESHOLD = 0.4


def _risk_level(score: float) -> str:
    """Map a numeric churn score to a human-readable risk level."""
    if score > HIGH_RISK_THRESHOLD:
        return "high"
    elif score > MEDIUM_RISK_THRESHOLD:
        return "medium"
    return "low"


# ── Individual signal computers ───────────────────────────────────────────────

def _days_inactive_norm(last_active_str: str | None) -> float:
    """
    Normalise days inactive to a 0–1 scale, capped at 30 days.

    Args:
        last_active_str: ISO 8601 timestamp string from Supabase, or None.

    Returns:
        Float in [0.0, 1.0]. 0.0 = active today. 1.0 = inactive 30+ days.
    """
    if not last_active_str:
        return 1.0  # No activity on record — maximum inactive score

    try:
        last_active = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days = (now - last_active).days
        return min(days / 30.0, 1.0)
    except Exception as e:
        print(f"[WARN] Failed to parse last_active timestamp: {e}", file=sys.stderr)
        return 1.0


def _abandoned_enquiry_rate(customer_id: str, supabase: Client) -> float:
    """
    Compute the fraction of this student's enquiries that were abandoned.

    Queries enquiry_events table for:
      - Total enquiries (all statuses)
      - Abandoned enquiries (status = 'abandoned')

    Args:
        customer_id: The student's UUID from the customers table.
        supabase:    Supabase client.

    Returns:
        Float in [0.0, 1.0]. 0.0 = never abandoned. 1.0 = always abandons.
    """
    try:
        total_resp = (
            supabase.table("enquiry_events")
            .select("id", count="exact")
            .eq("customer_id", customer_id)
            .execute()
        )
        total = total_resp.count or 0

        abandoned_resp = (
            supabase.table("enquiry_events")
            .select("id", count="exact")
            .eq("customer_id", customer_id)
            .eq("status", "abandoned")
            .execute()
        )
        abandoned = abandoned_resp.count or 0

        return abandoned / max(total, 1)

    except Exception as e:
        print(f"[WARN] Failed to compute abandoned enquiry rate: {e}", file=sys.stderr)
        return 0.0


def _message_drop_rate(customer_id: str, supabase: Client) -> float:
    """
    Compute how much the student's message frequency has dropped.

    Compares:
      - last7:  messages sent in the last 7 days
      - prior7: messages sent in the 7 days before that

    Formula: 1 - (last7 / max(prior7, 1)), clipped to [0, 1]

    Args:
        customer_id: The student's UUID.
        supabase:    Supabase client.

    Returns:
        Float in [0.0, 1.0]. 0.0 = no drop (or increasing). 1.0 = complete silence.
    """
    try:
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        last7_start  = (now - timedelta(days=7)).isoformat()
        prior7_start = (now - timedelta(days=14)).isoformat()
        prior7_end   = last7_start

        last7_resp = (
            supabase.table("conversations")
            .select("id", count="exact")
            .eq("customer_id", customer_id)
            .eq("direction", "inbound")
            .gte("timestamp", last7_start)
            .execute()
        )
        last7 = last7_resp.count or 0

        prior7_resp = (
            supabase.table("conversations")
            .select("id", count="exact")
            .eq("customer_id", customer_id)
            .eq("direction", "inbound")
            .gte("timestamp", prior7_start)
            .lt("timestamp", prior7_end)
            .execute()
        )
        prior7 = prior7_resp.count or 0

        rate = 1.0 - (last7 / max(prior7, 1))
        return max(0.0, min(rate, 1.0))  # Clip to [0, 1]

    except Exception as e:
        print(f"[WARN] Failed to compute message drop rate: {e}", file=sys.stderr)
        return 0.0


# ── Main public function ──────────────────────────────────────────────────────

def compute_churn_score(phone_number: str, supabase: Client) -> dict:
    """
    Compute a complete churn score for a student identified by phone number.

    Churn score formula:
        score = (0.5 × days_inactive_norm)
              + (0.3 × abandoned_enquiry_rate)
              + (0.2 × message_drop_rate)

    Args:
        phone_number: The student's WhatsApp phone number (e.g. '+919876543210').
        supabase:     Supabase client.

    Returns:
        Dict:
          {
            "churn_score": float,          # 0.0 – 1.0
            "risk_level":  str,            # "high" | "medium" | "low"
          }
    """
    try:
        # Fetch customer record
        resp = (
            supabase.table("customers")
            .select("id, last_active")
            .eq("phone_number", phone_number)
            .limit(1)
            .execute()
        )
        customer = resp.data[0] if resp.data else None

        if not customer:
            print(f"[WARN] No customer found for {phone_number}", file=sys.stderr)
            return {"churn_score": 0.0, "risk_level": "low"}

        customer_id   = customer["id"]
        last_active   = customer.get("last_active")

        # Compute the three signals
        s1 = _days_inactive_norm(last_active)
        s2 = _abandoned_enquiry_rate(customer_id, supabase)
        s3 = _message_drop_rate(customer_id, supabase)

        # Weighted churn score
        score = round((0.5 * s1) + (0.3 * s2) + (0.2 * s3), 4)

        return {
            "churn_score": score,
            "risk_level":  _risk_level(score),
        }

    except Exception as e:
        print(f"[ERROR] compute_churn_score failed for {phone_number}: {e}", file=sys.stderr)
        return {"churn_score": 0.0, "risk_level": "low"}
