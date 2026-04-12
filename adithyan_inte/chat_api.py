"""
chat_api.py
-----------
REST API endpoints for the Business Owner Dashboard (Frontend).

Exposes chat history, customer list, and conversation threads
so the frontend engineer can build the chat history viewer.

All endpoints are READ-ONLY — no mutation of data from the frontend side.

Base URL: http://your-server:5000/api/v1/...

Endpoints:
  GET /api/v1/customers                    — list all customers
  GET /api/v1/customers/<identifier>       — single customer profile
  GET /api/v1/conversations                — all conversations (paginated)
  GET /api/v1/conversations/<identifier>   — full chat thread for one user
  GET /api/v1/stats                        — dashboard summary stats
"""

import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from supabase_client import supabase

logger = logging.getLogger(__name__)

# Register as a Flask Blueprint — mounted at /api/v1 in app.py
chat_api = Blueprint("chat_api", __name__, url_prefix="/api/v1")


# ─────────────────────────────────────────────────────────────────────────────
# 1. List all customers
#    GET /api/v1/customers
#    GET /api/v1/customers?channel=telegram
#    GET /api/v1/customers?risk=high
#    GET /api/v1/customers?search=Adithyan
# ─────────────────────────────────────────────────────────────────────────────

@chat_api.route("/customers", methods=["GET"])
def list_customers():
    """
    Returns all customers with their profile data.

    Query params:
      channel  — filter by 'telegram' | 'whatsapp'
      risk     — filter by 'low' | 'medium' | 'high'
      search   — search by name or phone number (partial match)
      limit    — max records to return (default 50)
      offset   — for pagination (default 0)
    """
    try:
        channel = request.args.get("channel")
        risk    = request.args.get("risk")
        search  = request.args.get("search")
        limit   = int(request.args.get("limit", 50))
        offset  = int(request.args.get("offset", 0))

        query = (
            supabase.table("customers")
            .select(
                "id, phone_number, name, channel, churn_score, "
                "risk_level, is_handoff_active, last_active, created_at"
            )
            .order("last_active", desc=True)
            .range(offset, offset + limit - 1)
        )

        if channel:
            query = query.eq("channel", channel)
        if risk:
            query = query.eq("risk_level", risk)

        result = query.execute()
        customers = result.data or []

        # Search filter (in-memory since Supabase free plan lacks full-text)
        if search:
            s = search.lower()
            customers = [
                c for c in customers
                if s in (c.get("name") or "").lower()
                or s in (c.get("phone_number") or "").lower()
            ]

        return jsonify({
            "success": True,
            "count": len(customers),
            "offset": offset,
            "limit": limit,
            "customers": customers,
        }), 200

    except Exception as exc:
        logger.error("[API] list_customers error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 2. Single Customer Profile
#    GET /api/v1/customers/<phone_or_chat_id>
# ─────────────────────────────────────────────────────────────────────────────

@chat_api.route("/customers/<identifier>", methods=["GET"])
def get_customer(identifier: str):
    """
    Returns a single customer's full profile.
    identifier = phone number (WhatsApp) or chat_id (Telegram)
    """
    try:
        result = (
            supabase.table("customers")
            .select("*")
            .eq("phone_number", identifier)
            .execute()
        )
        if not result.data:
            return jsonify({"success": False, "error": "Customer not found"}), 404

        return jsonify({"success": True, "customer": result.data[0]}), 200

    except Exception as exc:
        logger.error("[API] get_customer error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 3. Full Chat Thread for One User
#    GET /api/v1/conversations/<phone_or_chat_id>
#    GET /api/v1/conversations/<id>?limit=50&before=2026-04-12T00:00:00Z
# ─────────────────────────────────────────────────────────────────────────────

@chat_api.route("/conversations/<identifier>", methods=["GET"])
def get_conversation_thread(identifier: str):
    """
    Returns the complete chat history for a single user, oldest-first
    (so the frontend can render it like a WhatsApp/Telegram chat bubble UI).

    Query params:
      limit   — max messages to return (default 100)
      before  — ISO timestamp — only return messages before this time
                (use the oldest message's created_at for pagination)
    """
    try:
        limit  = int(request.args.get("limit", 100))
        before = request.args.get("before")

        query = (
            supabase.table("conversations")
            .select("id, phone_number, message_text, direction, created_at")
            .eq("phone_number", identifier)
            .order("created_at", desc=False)   # oldest first = natural chat order
            .limit(limit)
        )

        if before:
            query = query.lt("created_at", before)

        result = query.execute()
        messages = result.data or []

        # Enrich with bubble metadata
        enriched = []
        for msg in messages:
            enriched.append({
                "id":           msg.get("id"),
                "text":         msg.get("message_text"),
                "direction":    msg.get("direction"),   # "inbound" | "outbound"
                "sender":       "user" if msg.get("direction") == "inbound" else "bot",
                "timestamp":    msg.get("created_at"),
                "phone_number": msg.get("phone_number"),
            })

        return jsonify({
            "success":    True,
            "identifier": identifier,
            "count":      len(enriched),
            "messages":   enriched,
        }), 200

    except Exception as exc:
        logger.error("[API] get_conversation_thread error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 4. All Conversations (Paginated) — for the "Inbox" view
#    GET /api/v1/conversations
#    GET /api/v1/conversations?limit=20&offset=0
# ─────────────────────────────────────────────────────────────────────────────

@chat_api.route("/conversations", methods=["GET"])
def list_conversations():
    """
    Returns the latest message per customer — the "inbox" summary view.
    Perfect for the sidebar list in a chat dashboard.

    Returns each unique customer with:
      - their last message text
      - direction (inbound/outbound)
      - timestamp of last message
      - customer name
    """
    try:
        limit  = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        # Get all recent conversations
        conv_result = (
            supabase.table("conversations")
            .select("phone_number, message_text, direction, created_at")
            .order("created_at", desc=True)
            .range(offset, offset + limit * 5)   # over-fetch to deduplicate
            .execute()
        )
        rows = conv_result.data or []

        # Deduplicate — keep only the LATEST message per user (inbox view)
        seen = {}
        for row in rows:
            uid = row["phone_number"]
            if uid not in seen:
                seen[uid] = row

        inbox = list(seen.values())[:limit]

        # Enrich with customer names from customers table
        if inbox:
            phone_numbers = [r["phone_number"] for r in inbox]
            cust_result = (
                supabase.table("customers")
                .select("phone_number, name, channel, risk_level, is_handoff_active")
                .in_("phone_number", phone_numbers)
                .execute()
            )
            cust_map = {c["phone_number"]: c for c in (cust_result.data or [])}

            for row in inbox:
                uid  = row["phone_number"]
                cust = cust_map.get(uid, {})
                row["name"]              = cust.get("name", uid)
                row["channel"]           = cust.get("channel", "unknown")
                row["risk_level"]        = cust.get("risk_level", "low")
                row["is_handoff_active"] = cust.get("is_handoff_active", False)

        return jsonify({
            "success":       True,
            "count":         len(inbox),
            "conversations": inbox,
        }), 200

    except Exception as exc:
        logger.error("[API] list_conversations error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 5. Dashboard Stats
#    GET /api/v1/stats
# ─────────────────────────────────────────────────────────────────────────────

@chat_api.route("/stats", methods=["GET"])
def dashboard_stats():
    """
    Returns high-level summary for the business owner dashboard.

    Returns:
      total_customers, telegram_users, whatsapp_users,
      high_risk_count, active_handoffs, total_messages
    """
    try:
        # Total customers
        total = supabase.table("customers").select("id", count="exact").execute()

        # By channel
        tg   = supabase.table("customers").select("id", count="exact").eq("channel", "telegram").execute()
        wa   = supabase.table("customers").select("id", count="exact").eq("channel", "whatsapp").execute()

        # High risk
        high = supabase.table("customers").select("id", count="exact").eq("risk_level", "high").execute()

        # Active handoffs
        hoff = supabase.table("customers").select("id", count="exact").eq("is_handoff_active", True).execute()

        # Total messages
        msgs = supabase.table("conversations").select("id", count="exact").execute()

        return jsonify({
            "success": True,
            "stats": {
                "total_customers":  total.count,
                "telegram_users":   tg.count,
                "whatsapp_users":   wa.count,
                "high_risk_count":  high.count,
                "active_handoffs":  hoff.count,
                "total_messages":   msgs.count,
            }
        }), 200

    except Exception as exc:
        logger.error("[API] dashboard_stats error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500
