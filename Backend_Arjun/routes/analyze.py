from flask import Blueprint, request, jsonify
import sys
import traceback

analyze_bp = Blueprint("analyze_bp", __name__)

@analyze_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    POST /analyze
    Receives {phone_number, message_text}
    Returns {intent, sentiment, language, action, churn_score, risk_level, preferred_country}
    """
    # Import inside the function or at the top if no circular imports
    from app import supabase, llm
    from intelligence import detect_language, detect_intent, detect_sentiment
    from rag import retrieve_context
    from churn_scorer import compute_churn_score
    from decision_engine import decide_action

    try:
        data = request.json or {}
        phone_number = data.get("phone_number")
        message_text = data.get("message_text")

        if not phone_number or not message_text:
            return jsonify({"error": "phone_number and message_text required"}), 400

        # 1. Detect language
        language = detect_language(message_text)

        # 2. Fetch customer profile to get preferred_country
        preferred_country = None
        has_active_enquiry = False
        
        customer_resp = supabase.table("customers").select("id, preferred_country").eq("phone_number", phone_number).execute()
        customer = customer_resp.data[0] if customer_resp.data else None
        
        if customer:
            preferred_country = customer.get("preferred_country")
            # Check for active enquiry
            enq_resp = supabase.table("enquiry_events").select("id").eq("customer_id", customer["id"]).eq("status", "active").execute()
            has_active_enquiry = len(enq_resp.data) > 0

        # 3. Retrieve context (RAG)
        context = retrieve_context(message_text, supabase, filter_country=preferred_country)

        # 4. Detect Intent
        intent = detect_intent(message_text, context=context, llm=llm)

        # 5. Detect Sentiment
        sentiment = detect_sentiment(message_text, llm=llm)

        # 6. Compute Churn Score
        churn_data = compute_churn_score(phone_number, supabase)
        churn_score = churn_data.get("churn_score", 0.0)
        risk_level = churn_data.get("risk_level", "low")

        # 7. Decide Action
        action = decide_action(
            intent=intent,
            sentiment=sentiment,
            churn_score=churn_score,
            has_active_enquiry=has_active_enquiry
        )

        return jsonify({
            "intent": intent,
            "sentiment": sentiment,
            "language": language,
            "action": action,
            "churn_score": churn_score,
            "risk_level": risk_level,
            "preferred_country": preferred_country
        }), 200

    except Exception as e:
        print(f"[ERROR] /analyze failed: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
