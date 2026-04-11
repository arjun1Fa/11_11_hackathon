from flask import Blueprint, request, jsonify
import sys
import traceback

generate_reply_bp = Blueprint("generate_reply_bp", __name__)

@generate_reply_bp.route("/generate-reply", methods=["POST"])
def generate_reply_endpoint():
    """
    POST /generate-reply
    Receives {phone_number, message_text, intent, sentiment, language}
    Returns {reply_text}
    """
    from app import supabase, llm
    from rag import retrieve_context
    from reply_generator import generate_reply

    try:
        data = request.json or {}
        phone_number = data.get("phone_number")
        message_text = data.get("message_text")
        intent = data.get("intent", "general")
        sentiment = data.get("sentiment", "neutral")
        language = data.get("language", "en")

        if not phone_number or not message_text:
            return jsonify({"error": "phone_number and message_text required"}), 400

        # 1. Fetch student_profile
        profile = {}
        customer_resp = supabase.table("customers").select("*").eq("phone", phone_number).execute()
        if customer_resp.data:
            profile = customer_resp.data[0]

        # 2. Retrieve contextual info
        preferred_country = profile.get("preferred_country")
        rag_context = retrieve_context(message_text, supabase, filter_country=preferred_country)

        # 3. Generate Reply
        reply_text = generate_reply(
            message_text=message_text,
            intent=intent,
            sentiment=sentiment,
            language=language,
            student_profile=profile,
            rag_context=rag_context,
            llm=llm
        )

        return jsonify({"reply_text": reply_text}), 200

    except Exception as e:
        print(f"[ERROR] /generate-reply failed: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
