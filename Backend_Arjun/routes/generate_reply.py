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
    from rag import retrieve_context, get_chat_history
    from reply_generator import generate_reply, onboarding_reply
    from intelligence import extract_profile_data

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
        customer_resp = supabase.table("customers").select("*").eq("phone_number", phone_number).execute()
        if customer_resp.data:
            profile = customer_resp.data[0]

        # 1.3 AUTO-CREATE USER
        if not profile:
            try:
                new_user_resp = supabase.table("customers").insert({"phone_number": phone_number}).execute()
                if new_user_resp.data:
                    profile = new_user_resp.data[0]
            except Exception as e:
                print(f"[WARN] Failed to auto-create user in generate_reply: {e}", file=sys.stderr)

        # 1.5 FAILSAFE: If the Integration Engineer skips /analyze, we extract the data here!
        if profile:
            extracted_data = extract_profile_data(message_text, llm)
            if extracted_data:
                try:
                    supabase.table("customers").update(extracted_data).eq("id", profile["id"]).execute()
                    for k, v in extracted_data.items():
                        profile[k] = v
                except Exception as db_err:
                    print(f"[WARN] Failed to auto-update profile in generate_reply: {db_err}", file=sys.stderr)

        # 2. Check if onboarding is required
        onboarding_needed = False
        if not profile:
            onboarding_needed = True
        else:
            required_fields = ["name", "preferred_country", "education_level", "field_of_study", "ielts_score"]
            for field in required_fields:
                if profile.get(field) is None:
                    onboarding_needed = True
                    break

        if onboarding_needed:
            reply_text = onboarding_reply(
                message_text=message_text,
                language=language,
                student_profile=profile,
                llm=llm
            )
        else:
            # 3. Retrieve contextual info
            rag_context = retrieve_context(message_text, supabase)
            chat_history = get_chat_history(profile.get("id"), supabase) if profile else ""

            # 4. Generate Standard Reply
            reply_text = generate_reply(
                message_text=message_text,
                intent=intent,
                sentiment=sentiment,
                language=language,
                student_profile=profile,
                rag_context=rag_context,
                chat_history=chat_history,
                llm=llm
            )

        # 5. Native Human Handoff Trigger
        # If the AI hit the anti-hallucination guardrail, instantly flag this user for human intervention
        if "I will need to check with a senior counsellor" in reply_text and profile:
            try:
                supabase.table("customers").update({"is_handoff_active": True}).eq("id", profile["id"]).execute()
            except Exception as e:
                print(f"[WARN] Failed to trigger human handoff in DB: {e}", file=sys.stderr)

        return jsonify({"reply_text": reply_text}), 200

    except Exception as e:
        print(f"[ERROR] /generate-reply failed: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
