from flask import Blueprint, request, jsonify
import sys
import traceback

upsell_bp = Blueprint("upsell_bp", __name__)

@upsell_bp.route("/upsell", methods=["POST"])
def upsell_endpoint():
    """
    POST /upsell
    Receives {phone_number, message_text}
    Returns {upsell_message}
    """
    from app import supabase, llm
    from rag import retrieve_context, get_chat_history
    from reply_generator import upsell_reply
    from intelligence import detect_language

    try:
        data = request.json or {}
        phone_number = data.get("phone_number")
        message_text = data.get("message_text")

        if not phone_number or not message_text:
            return jsonify({"error": "phone_number and message_text required"}), 400

        # Fetch student_profile
        profile = {}
        customer_resp = supabase.table("customers").select("*").eq("phone_number", phone_number).execute()
        if customer_resp.data:
            profile = customer_resp.data[0]

        language = detect_language(message_text)
        preferred_country = profile.get("preferred_country")
        
        # Retrieve context mapped to their country (to find upsell opportunities like scholarships)
        rag_context = retrieve_context(message_text, supabase, filter_country=preferred_country)
        chat_history = get_chat_history(profile.get("id"), supabase) if profile else ""

        # Generate upsell reply
        upsell_message = upsell_reply(
            message_text=message_text,
            language=language,
            student_profile=profile,
            rag_context=rag_context,
            chat_history=chat_history,
            llm=llm
        )

        return jsonify({"upsell_message": upsell_message}), 200

    except Exception as e:
        print(f"[ERROR] /upsell failed: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
