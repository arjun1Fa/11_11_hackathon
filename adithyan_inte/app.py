"""
app.py
------
Flask Server for Smartilee — Integration & Orchestration Layer (WhatsApp Direct).
"""

import os
import logging
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv

load_dotenv()

from adithyan_inte.whatsapp import verify_webhook, parse_inbound_message
from adithyan_inte.orchestrator import process_whatsapp_message
from adithyan_inte.automation import scheduler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ── WhatsApp Webhook: Verification (GET) ──────────────────────────────────────

@app.route("/webhook", methods=["GET"])
def webhook_verify():
    """Endpoint for Meta to verify our webhook URL."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    result = verify_webhook(mode, token, challenge)
    if result:
        return Response(result, mimetype="text/plain"), 200
    return "Verification failed", 403

# ── WhatsApp Webhook: Message Reception (POST) ────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook_message():
    """Receiver for all WhatsApp events from Meta."""
    data = request.json
    
    # 1. Parse Meta's payload structure
    msg_info = parse_inbound_message(data)
    
    if msg_info:
        # 2. Hand off to orchestrator for processing (bridge to AI backend)
        process_whatsapp_message(
            phone_number=msg_info["phone_number"],
            message_text=msg_info["message_text"],
            wa_msg_id=msg_info["wa_msg_id"]
        )
        
    # Always return 200 to Meta to acknowledge receipt
    return jsonify({"status": "ok"}), 200

# ── Service Endpoints ─────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "integration_layer",
        "channels": ["whatsapp_direct"]
    })

if __name__ == "__main__":
    # Start background scheduler for enquiry events
    if not scheduler.running:
        scheduler.start()
        
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
