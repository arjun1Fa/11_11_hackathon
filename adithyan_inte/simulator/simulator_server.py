"""
simulator_server.py
-------------------
Smartilee — WhatsApp Business Simulator
A fake Meta endpoint for local testing and hackathon demo.

This server:
  1. Serves a WhatsApp Web-like UI.
  2. Accepts messages from the UI and forwards them to the Integration Layer
     formatted as proper Meta JSON payloads.
  3. Uses IN-MEMORY storage for messages — no Supabase schema required.
     If your backend sends replies back to a /receive endpoint, they show up too.

Run with:
    python simulator_server.py

Access the UI at:
    http://localhost:5050
"""

import os
import time
import uuid
import logging
import requests
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

# Load env from parent folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')

# ── Config ────────────────────────────────────────────────────────────────────
INTEGRATION_WEBHOOK_URL = os.getenv("INTEGRATION_WEBHOOK_URL", "http://localhost:5000/webhook")
SIMULATOR_PHONE = os.getenv("SIMULATOR_PHONE", "919999999999")
SIMULATOR_NAME = os.getenv("SIMULATOR_NAME", "Test Student")

# ── In-Memory Message Store ───────────────────────────────────────────────────
# This replaces Supabase polling — works instantly, no schema needed.
message_store = []

def store_message(text, direction, metadata=None):
    msg = {
        "id": str(uuid.uuid4()),
        "message_text": text,
        "direction": direction,   # inbound = student, outbound = AI
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ai_metadata": metadata or {}
    }
    message_store.append(msg)
    return msg

# ── Serve UI ──────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ── Send: Student → Integration Layer ─────────────────────────────────────────
@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    message_text = data.get('message', '').strip()
    phone = data.get('phone', SIMULATOR_PHONE)

    if not message_text:
        return jsonify({"error": "Empty message"}), 400

    wa_msg_id = f"wamid.sim_{uuid.uuid4().hex[:16]}"

    # Store student message (inbound from WA perspective)
    store_message(message_text, "inbound")

    # Build exact Meta webhook JSON
    meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "SIM_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15550000001",
                        "phone_number_id": "SIM_PHONE_ID"
                    },
                    "contacts": [{"profile": {"name": SIMULATOR_NAME}, "wa_id": phone}],
                    "messages": [{
                        "from": phone,
                        "id": wa_msg_id,
                        "timestamp": str(int(time.time())),
                        "text": {"body": message_text},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    logger.info("[SIM →] %s", message_text)

    try:
        response = requests.post(INTEGRATION_WEBHOOK_URL, json=meta_payload, timeout=15)
        logger.info("[SIM] Integration layer status: %d", response.status_code)
        return jsonify({
            "status": "forwarded",
            "wa_msg_id": wa_msg_id,
            "integration_status": response.status_code
        })
    except requests.ConnectionError:
        logger.error("[SIM] Integration layer not reachable at %s", INTEGRATION_WEBHOOK_URL)
        return jsonify({"error": f"Integration layer not reachable at {INTEGRATION_WEBHOOK_URL}. Is app.py running on port 5000?"}), 503
    except requests.Timeout:
        return jsonify({"error": "Integration layer timed out after 15s"}), 504
    except Exception as exc:
        logger.error("[SIM] Unexpected error: %s", exc)
        return jsonify({"error": str(exc)}), 500

# ── Global JSON Error Handlers (prevent HTML error pages reaching the UI) ─────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "path": str(e)}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# ── Receive: AI Reply → Simulator (Optional Hook) ─────────────────────────────
@app.route('/receive', methods=['POST'])
def receive_reply():
    """
    Optional: Your integration layer can POST replies back here instead of /
    calling the real Meta Graph API. This instantly shows them in the UI.
    Set MOCK_WHATSAPP_REPLY_URL=http://localhost:5050/receive in the integration layer.
    """
    data = request.json
    text = data.get('text') or data.get('body') or data.get('message', '')
    metadata = data.get('metadata', {})
    if text:
        store_message(text, "outbound", metadata)
        logger.info("[SIM ←] AI Reply stored: %s", text[:60])
    return jsonify({"status": "received"})

# ── Poll for Messages ─────────────────────────────────────────────────────────
@app.route('/messages', methods=['GET'])
def get_messages():
    since = request.args.get('since')
    if since:
        msgs = [m for m in message_store if m['created_at'] > since]
    else:
        msgs = list(message_store)
    return jsonify({"messages": msgs})

# ── Config ────────────────────────────────────────────────────────────────────
@app.route('/config')
def get_config():
    return jsonify({
        "simulator_phone": SIMULATOR_PHONE,
        "simulator_name": SIMULATOR_NAME,
        "integration_url": INTEGRATION_WEBHOOK_URL
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "whatsapp_simulator", "messages_stored": len(message_store)})

if __name__ == '__main__':
    port = int(os.getenv("SIMULATOR_PORT", 5050))
    ngrok_authtoken = os.getenv("NGROK_AUTHTOKEN", "")
    public_url = None

    # Auto-start ngrok tunnel if token is provided
    if ngrok_authtoken:
        try:
            from pyngrok import ngrok, conf
            conf.get_default().auth_token = ngrok_authtoken
            tunnel = ngrok.connect(port, "http")
            public_url = tunnel.public_url
        except Exception as e:
            print(f"  ⚠️  ngrok failed to start: {e}")
    else:
        try:
            from pyngrok import ngrok as _ngrok
            tunnel = _ngrok.connect(port, "http")
            public_url = tunnel.public_url
        except Exception:
            pass  # No token, no tunnel — local only

    print(f"\n{'='*55}")
    print(f"  🟢 WhatsApp Simulator   →  http://localhost:{port}")
    print(f"  📡 Integration Layer    →  {INTEGRATION_WEBHOOK_URL}")
    print(f"  📞 Simulated Phone      →  {SIMULATOR_PHONE}")
    if public_url:
        print(f"  🌍 Public ngrok URL     →  {public_url}")
        print(f"  🔗 Share this for demo  →  {public_url}")
    else:
        print(f"  ℹ️  Add NGROK_AUTHTOKEN to .env for a public URL")
    print(f"{'='*55}\n")
    app.run(host='0.0.0.0', port=port, debug=False)

