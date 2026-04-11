"""
churn_scorer.py
---------------
Weighted churn formula for study abroad students.
"""

import logging
from datetime import datetime, timezone, timedelta
from adithyan_inte.supabase_client import supabase

logger = logging.getLogger(__name__)

def compute_churn_score(phone_number: str) -> dict:
    """
    score = (0.5 * days_inactive_norm) + (0.3 * abandoned_enquiry_rate) + (0.2 * message_drop_rate)
    """
    try:
        # 1. Fetch data from Supabase
        customer_res = supabase.table("customers").select("id, last_active").eq("phone_number", phone_number).single().execute()
        if not customer_res.data:
            return {"churn_score": 0.0, "risk_level": "low"}
            
        customer_id = customer_res.data["id"]
        last_active = datetime.fromisoformat(customer_res.data["last_active"].replace('Z', '+00:00'))
        
        # 2. Days Inactive Norm
        days_inactive = (datetime.now(timezone.utc) - last_active).days
        days_inactive_norm = min(days_inactive / 30, 1.0)
        
        # 3. Abandoned Enquiry Rate
        enquiry_res = supabase.table("enquiry_events").select("status").eq("customer_id", customer_id).execute()
        enquiries = enquiry_res.data or []
        total_enquiries = len(enquiries)
        abandoned_enquiries = len([e for e in enquiries if e["status"] == "abandoned"])
        abandoned_rate = abandoned_enquiries / max(total_enquiries, 1)
        
        # 4. Message Drop Rate (Stubbed for now, normally uses last7 vs prior7 days)
        # Using a simple heuristic based on last active
        message_drop_rate = 0.5 if days_inactive > 7 else 0.0
        
        # Weighted formula
        score = (0.5 * days_inactive_norm) + (0.3 * abandoned_rate) + (0.2 * message_drop_rate)
        
        risk_level = "low"
        if score > 0.7: risk_level = "high"
        elif score > 0.4: risk_level = "medium"
        
        return {
            "churn_score": round(score, 2),
            "risk_level": risk_level
        }
        
    except Exception as exc:
        logger.error("Churn score computation failed: %s", exc)
        return {"churn_score": 0.0, "risk_level": "low"}
