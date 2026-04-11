"""
decision_engine.py
------------------
Routing logic for Smartilee.
Determines action based on intent, sentiment, churn, and active enquiries.
"""

def decide_action(intent, sentiment, churn_score, has_active_enquiry) -> str:
    """
    Returns: auto_reply, upsell, handoff, or schedule_followup.
    Priority rules:
    1. negative sentiment + complaint intent -> handoff
    2. high churn_score (> 0.7) -> schedule_followup
    3. package_enquiry + positive sentiment -> upsell
    4. active enquiry + package enquiry -> auto_reply
    5. Default -> auto_reply
    """
    
    # Rule 1: Escalation for unhappy customers
    if sentiment == "negative" and intent == "complaint":
        return "handoff"
        
    # Rule 2: Churn re-engagement trigger
    if churn_score > 0.7:
        return "schedule_followup"
        
    # Rule 3: Upsell opportunity
    if intent == "package_enquiry" and sentiment == "positive":
        return "upsell"
        
    # Rule 4: Standard customer enquiry maintenance
    if has_active_enquiry and intent == "package_enquiry":
        return "auto_reply"
        
    # Default Action
    return "auto_reply"
