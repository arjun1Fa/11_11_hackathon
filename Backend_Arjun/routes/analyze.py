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
    from intelligence import detect_language, detect_intent, detect_sentiment, extract_profile_data
    from rag import retrieve_context, get_chat_history
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
        
        customer_resp = supabase.table("customers").select("*").eq("phone_number", phone_number).execute()
        customer = customer_resp.data[0] if customer_resp.data else None
        
        # 2.5 AUTO-CREATE USER
        # If the integration engineer hasn't created the user, we will do it automatically!
        if not customer:
            try:
                new_user_resp = supabase.table("customers").insert({"phone_number": phone_number}).execute()
                if new_user_resp.data:
                    customer = new_user_resp.data[0]
            except Exception as e:
                print(f"[WARN] Failed to auto-create user: {e}", file=sys.stderr)

        if customer:
            preferred_country = customer.get("preferred_country")
            
            # 3. Pull chat history to give context to the extractor
            chat_history = get_chat_history(customer["id"], supabase)

            # Extract any new profile data from message and update Supabase
            extracted_data = extract_profile_data(message_text, chat_history, llm)
            if extracted_data:
                try:
                    supabase.table("customers").update(extracted_data).eq("id", customer["id"]).execute()
                    # Update local profile object so the rest of the flow sees it
                    for k, v in extracted_data.items():
                        customer[k] = v
                    preferred_country = customer.get("preferred_country")
                except Exception as db_err:
                    print(f"[WARN] Failed to auto-update profile: {db_err}", file=sys.stderr)

            # Check for active enquiry
            enq_resp = supabase.table("enquiry_events").select("id").eq("customer_id", customer["id"]).eq("status", "active").execute()
            has_active_enquiry = len(enq_resp.data) > 0

        # 4. Retrieve context (RAG)
        context = retrieve_context(message_text, supabase, filter_country=preferred_country)

        # 5. Detect Intent
        chat_hist_val = chat_history if 'chat_history' in locals() else ""
        intent = detect_intent(message_text, context=context, chat_history=chat_hist_val, llm=llm)

        # 6. Detect Sentiment
        sentiment = detect_sentiment(message_text, llm=llm)

        # 7. Compute Churn Score
        churn_data = compute_churn_score(phone_number, supabase)
        churn_score = churn_data.get("churn_score", 0.0)
        risk_level = churn_data.get("risk_level", "low")

        # 8. Decide Action
        action = decide_action(
            intent=intent,
            sentiment=sentiment,
            churn_score=churn_score,
            has_active_enquiry=has_active_enquiry,
            student_profile=customer
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
