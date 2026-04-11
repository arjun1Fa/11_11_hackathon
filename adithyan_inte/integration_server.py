"""
integration_server.py
---------------------
Smartilee — Integration & Orchestration Layer

This is the unified module that wires together all components:
  - supabase_client.py  : Database singleton
  - orchestrator.py     : AI pipeline & action routing
  - handoff.py          : Human escalation logic
  - messaging.py        : Outbound message abstraction
  - automation.py       : APScheduler background jobs

Run this file directly, or import `app` for use with Gunicorn/uWSGI.

    python integration_server.py
    gunicorn integration_server:app
"""

# Re-export the Flask `app` object so Gunicorn can use this as its entry point
from app import app, scheduler  # noqa: F401

import logging
import os

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Start the background scheduler
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started — background jobs active.")

    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    logger.info(
        "Smartilee Integration Server ready on http://0.0.0.0:%d", port
    )
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
