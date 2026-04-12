"""
decision_engine.py
Routes every student interaction to exactly one action based on
intent, sentiment, churn score, and active enquiry status.
"""


# ── Action constants ──────────────────────────────────────────────────────────

ACTION_AUTO_REPLY       = "auto_reply"
ACTION_UPSELL           = "upsell"
ACTION_HANDOFF          = "handoff"
ACTION_SCHEDULE_FOLLOWUP = "schedule_followup"
ACTION_ONBOARDING       = "onboarding"


def decide_action(
    intent: str,
    sentiment: str,
    churn_score: float,
    has_active_enquiry: bool,
    student_profile: dict = None,
) -> str:
    """
    Determine the correct action for this student message based on four signals.

    Priority rules (evaluated top to bottom — first match wins):

    1. Negative sentiment AND complaint intent → handoff
       The student is upset. A human counsellor must handle this immediately.

    2. Churn score > 0.7 → schedule_followup
       Student is at high risk of leaving. Trigger a re-engagement flow.

    3. package_enquiry AND positive sentiment → upsell
       Student is engaged and interested. Good moment to introduce an upgrade
       or a scholarship they haven't asked about.

    4. has_active_enquiry AND package_enquiry → auto_reply
       Student has an open enquiry; just answer their question directly.

    5. Default → auto_reply
       All other cases — let the AI handle it.

    Args:
        intent:             One of the 6 intent labels from intelligence.py.
        sentiment:          'positive', 'neutral', or 'negative'.
        churn_score:        Float 0.0–1.0 from churn_scorer.py.
        has_active_enquiry: True if student has an active enquiry in enquiry_events.

    Returns:
        One of: auto_reply, upsell, handoff, schedule_followup.
    """

    # Rule 0 — Incomplete profile → force onboarding
    if not student_profile:
        return ACTION_ONBOARDING

    required_fields = ["name", "preferred_country", "education_level", "field_of_study", "ielts_score"]
    for field in required_fields:
        if student_profile.get(field) is None:
            return ACTION_ONBOARDING

    # Rule 1 — Unhappy student with a complaint → human handoff immediately
    if sentiment == "negative" and intent == "complaint":
        return ACTION_HANDOFF

    # Rule 2 — High churn risk → proactive re-engagement, not a live reply
    if churn_score > 0.7:
        return ACTION_SCHEDULE_FOLLOWUP

    # Rule 3 — Engaged student asking about packages → upsell opportunity
    if intent == "package_enquiry" and sentiment == "positive":
        return ACTION_UPSELL

    # Rule 4 — Active enquiry + package question → just give them the answer
    if has_active_enquiry and intent == "package_enquiry":
        return ACTION_AUTO_REPLY

    # Rule 5 — Default: AI handles everything else automatically
    return ACTION_AUTO_REPLY
