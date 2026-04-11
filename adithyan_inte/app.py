"""
app.py
------
Smartilee — Integration & Orchestration Layer
Flask entry point.

Endpoints:
  GET  /webhook           — WhatsApp webhook verification (Meta handshake)
  POST /webhook           — Inbound WhatsApp messages from Meta
  POST /process-message   — Direct API for web/internal message injection
  GET  /health            — Server & scheduler health check
  GET  /scheduler/jobs    — (debug) list active APScheduler jobs
"""

import logging
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from adithyan_inte.orchestrator import process_message
from adithyan_inte.automation import scheduler
from adithyan_inte.whatsapp import verify_webhook, parse_inbound_message, mark_message_read

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────────
# WhatsApp Business Cloud API Webhook
# ───────────────────────────────────────────────────────────────────────────────

@app.route("/webhook", methods=["GET"])
def whatsapp_verify():
    """
    Step 1 of WhatsApp setup — Meta calls this once when you register
    your webhook URL in the Meta Developer Console.

    Meta sends:
      ?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=RANDOM

    We echo back hub.challenge to confirm ownership.
    """
    challenge, status_code = verify_webhook(request.args)
    if status_code == 200:
        return challenge, 200
    return jsonify({"status": "error", "message": "Verification failed"}), 403


@app.route("/webhook", methods=["POST"])
def whatsapp_inbound():
    """
    Receives all WhatsApp events from Meta:
      — Inbound messages from customers
      — Delivery / read status updates

    IMPORTANT: Meta requires HTTP 200 within 5 seconds or it will retry.
    All AI processing happens inline here (keep AI backend fast), but
    the 200 is returned after each message is processed.

    Flow per message:
      1. Parse payload → extract phone_number + message_text
      2. Mark as read  → shows double blue ticks on customer's phone
      3. Run full orchestration pipeline (orchestrator.py)
      4. Reply is sent back by orchestrator via messaging.py → whatsapp.py
    """
    payload = request.get_json(silent=True)

    if not payload:
        # Always return 200 to Meta even for malformed payloads
        logger.warning("WhatsApp webhook received non-JSON body.")
        return jsonify({"status": "ok"}), 200

    messages = parse_inbound_message(payload)

    if not messages:
        # Status update (sent/delivered/read) — nothing to process
        return jsonify({"status": "ok"}), 200

    for msg in messages:
        phone_number    = msg["phone_number"]
        message_text    = msg["message_text"]
        wa_msg_id       = msg["whatsapp_msg_id"]
        contact_name    = msg["contact_name"]

        logger.info(
            "WhatsApp inbound — from=%s name='%s' | text='%s'",
            phone_number, contact_name, message_text[:60],
        )

        # Show blue double-ticks immediately so customer knows we received it
        mark_message_read(wa_msg_id)

        # Run the full AI orchestration pipeline
        try:
            process_message(
                phone_number=phone_number,
                message_text=message_text,
                source="whatsapp",
            )
        except Exception as exc:
            logger.exception(
                "Error processing WhatsApp message from %s: %s", phone_number, exc
            )
            # Do NOT return 500 — always 200 to Meta to prevent retries

    return jsonify({"status": "ok"}), 200


# ───────────────────────────────────────────────────────────────────────────────
# Direct API (web / internal injection)
# ───────────────────────────────────────────────────────────────────────────────

@app.route("/process-message", methods=["POST"])
def process_message_endpoint():
    """
    Main message orchestration pipeline.

    Request body (JSON):
    {
        "phone_number": "+919876543210",
        "message_text": "I'm interested in the 2BHK unit",
        "source":       "web"          // or "whatsapp"
    }

    Response:
    {
        "status":     "ok",
        "action":     "auto_reply",    // what the system did
        "response":   "Great! Let me ...",  // outbound text (if any)
        "handoff_id": null             // UUID if handoff triggered
    }
    """
    data = request.get_json(silent=True)

    # ── Input validation ──────────────────────────────────────────────────
    if not data:
        return (
            jsonify({"status": "error", "message": "Request body must be JSON."}),
            400,
        )

    phone_number = (data.get("phone_number") or "").strip()
    message_text = (data.get("message_text") or "").strip()
    source = (data.get("source") or "web").strip().lower()

    if not phone_number:
        return (
            jsonify({"status": "error", "message": "Missing required field: phone_number"}),
            400,
        )

    if not message_text:
        return (
            jsonify({"status": "error", "message": "Missing required field: message_text"}),
            400,
        )

    if source not in ("web", "whatsapp"):
        return (
            jsonify({"status": "error", "message": "source must be 'web' or 'whatsapp'"}),
            400,
        )

    # ── Orchestration (all heavy lifting in orchestrator.py) ─────────────
    logger.info("Inbound message — from=%s | source=%s", phone_number, source)

    try:
        result = process_message(
            phone_number=phone_number,
            message_text=message_text,
            source=source,
        )
        return jsonify(result), 200

    except Exception as exc:
        logger.exception("Unhandled error in /process-message: %s", exc)
        return (
            jsonify({"status": "error", "message": "Internal server error. Check logs."}),
            500,
        )


@app.route("/health", methods=["GET"])
def health():
    """
    Basic health probe.

    Returns:
    {
        "status":    "ok",
        "timestamp": "2026-04-11T07:00:00+00:00",
        "scheduler": {
            "running": true,
            "job_count": 2
        }
    }
    """
    sched_running = scheduler.running if scheduler else False
    job_count = len(scheduler.get_jobs()) if sched_running else 0

    return (
        jsonify(
            {
                "status": "ok",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "scheduler": {
                    "running": sched_running,
                    "job_count": job_count,
                },
            }
        ),
        200,
    )


@app.route("/scheduler/jobs", methods=["GET"])
def list_scheduler_jobs():
    """
    Debug endpoint — lists all registered APScheduler jobs.
    Disable or protect this behind auth in production.
    """
    if not scheduler.running:
        return jsonify({"status": "error", "message": "Scheduler is not running."}), 503

    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run_utc": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger),
            }
        )

    return jsonify({"status": "ok", "jobs": jobs}), 200


# ── 404 handler ───────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(exc):
    return jsonify({"status": "error", "message": "Endpoint not found."}), 404


# ── 405 handler ───────────────────────────────────────────────────────────────
@app.errorhandler(405)
def method_not_allowed(exc):
    return jsonify({"status": "error", "message": "Method not allowed."}), 405


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Start background scheduler before the first request is served
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started.")

    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    logger.info("Smartilee Integration Server starting on port %d (debug=%s).", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
