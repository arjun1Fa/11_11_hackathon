"""
app.py
------
Flask Server for Smartilee — Integration & Orchestration Layer.
Supports: WhatsApp (Meta Direct) + Telegram Bot API.
"""

import os
import logging
import threading
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from whatsapp import verify_webhook, parse_inbound_message
from orchestrator import process_whatsapp_message, process_telegram_message
from telegram_bot import parse_telegram_update
from automation import scheduler
from chat_api import chat_api  # Dashboard API

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow frontend to call from any origin

# ── Register Blueprints ───────────────────────────────────────────────────────
app.register_blueprint(chat_api)  # mounts at /api/v1/...

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
        # Run orchestrator in a background thread to avoid Meta timeout (10s)
        thread = threading.Thread(
            target=process_whatsapp_message,
            kwargs={
                "phone_number": msg_info["phone_number"],
                "message_text": msg_info["message_text"],
                "wa_msg_id": msg_info["wa_msg_id"]
            }
        )
        thread.start()
        
    # Always return 200 to Meta to acknowledge receipt
    return jsonify({"status": "ok"}), 200

# ── Telegram Webhook: Message Reception (POST) ───────────────────────────────

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    """Receiver for all Telegram messages sent to the bot."""
    data = request.json

    msg_info = parse_telegram_update(data)

    if msg_info:
        # Run orchestrator in a background thread to avoid Telegram timeout
        thread = threading.Thread(
            target=process_telegram_message,
            kwargs={
                "chat_id": msg_info["chat_id"],
                "message_text": msg_info["message_text"],
                "telegram_msg_id": msg_info["telegram_msg_id"],
            }
        )
        thread.start()

    # Always return 200 to Telegram to acknowledge receipt
    return jsonify({"status": "ok"}), 200

# ── Service Endpoints ─────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "integration_layer",
        "channels": ["whatsapp_direct", "telegram"]
    })

if __name__ == "__main__":
    # Start background scheduler for enquiry events
    if not scheduler.running:
        scheduler.start()
        
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
