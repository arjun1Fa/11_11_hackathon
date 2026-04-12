from flask import Blueprint, request, jsonify
import sys
import traceback

churn_bp = Blueprint("churn_bp", __name__)

@churn_bp.route("/churn-score", methods=["POST"])
def churn_score_endpoint():
    """
    POST /churn-score
    Receives {phone_number}
    Returns {churn_score, risk_level}
    """
    from app import supabase
    from churn_scorer import compute_churn_score

    try:
        data = request.json or {}
        phone_number = data.get("phone_number")

        if not phone_number:
            return jsonify({"error": "phone_number required"}), 400

        result = compute_churn_score(phone_number, supabase)

        return jsonify(result), 200

    except Exception as e:
        print(f"[ERROR] /churn-score failed: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
