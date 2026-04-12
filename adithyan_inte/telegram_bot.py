"""
telegram_bot.py
---------------
Telegram Bot API integration for Smartilee.
Drop-in addition alongside whatsapp.py — both channels can run simultaneously.
"""

import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_BASE: str = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


# ── Parse Incoming Telegram Update ───────────────────────────────────────────

def parse_telegram_update(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parses a raw Telegram webhook update payload.

    Returns:
        { "chat_id": str, "message_text": str, "telegram_msg_id": str,
          "username": str, "first_name": str } or None
    """
    try:
        message = payload.get("message") or payload.get("edited_message")
        if not message:
            return None  # Could be a callback_query or channel_post — ignore

        chat_id = str(message["chat"]["id"])
        message_text = message.get("text", "")

        if not message_text:
            return None  # Ignore stickers, photos, voice notes, etc.

        from_user = message.get("from", {})
        first_name = from_user.get("first_name", "User")
        username   = from_user.get("username", "")

        return {
            "chat_id":        chat_id,
            "message_text":   message_text,
            "telegram_msg_id": str(message["message_id"]),
            "first_name":     first_name,
            "username":       username,
        }

    except (KeyError, TypeError) as exc:
        logger.debug("Telegram parse error: %s", exc)
        return None


# ── Send a Text Message ───────────────────────────────────────────────────────

def send_telegram_message(
    chat_id: str,
    message: str,
    reply_to_msg_id: Optional[str] = None,
) -> bool:
    """
    Sends a text message to a Telegram chat via Bot API.
    Supports Markdown formatting: *bold*, _italic_, `code`.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN missing in environment.")
        return False

    # Reload token dynamically (in case .env was loaded after module import)
    token = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload: Dict[str, Any] = {
        "chat_id":    chat_id,
        "text":       message,
        "parse_mode": "Markdown",
    }

    if reply_to_msg_id:
        payload["reply_to_message_id"] = int(reply_to_msg_id)

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Telegram send successful — chat_id=%s", chat_id)
        return True
    except requests.RequestException as exc:
        logger.error("Telegram send FAILED — chat_id=%s | error=%s", chat_id, exc)
        return False


# ── Send Typing Indicator ─────────────────────────────────────────────────────

def send_typing_action(chat_id: str) -> None:
    """Shows a 'typing…' bubble in the Telegram chat while AI is thinking."""
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
        requests.post(
            f"https://api.telegram.org/bot{token}/sendChatAction",
            json={"chat_id": chat_id, "action": "typing"},
            timeout=5,
        )
    except Exception:
        pass


# ── Register Webhook with Telegram ───────────────────────────────────────────

def register_webhook(public_url: str) -> bool:
    """
    Tells Telegram where to POST updates.
    Call once on server start (or whenever your ngrok URL changes).

    Args:
        public_url: Your public HTTPS URL (e.g. https://abc123.ngrok-free.app)
    """
    webhook_url = f"{public_url.rstrip('/')}/telegram"
    token = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    url   = f"https://api.telegram.org/bot{token}/setWebhook"

    try:
        response = requests.post(url, json={"url": webhook_url}, timeout=10)
        data = response.json()
        if data.get("ok"):
            logger.info("✅ Telegram webhook registered → %s", webhook_url)
            return True
        else:
            logger.error("❌ Webhook registration failed: %s", data)
            return False
    except Exception as exc:
        logger.error("Could not register Telegram webhook: %s", exc)
        return False


# ── Delete Webhook (switch to polling mode for local dev) ────────────────────

def delete_webhook() -> None:
    """Removes the webhook — useful when switching to polling during local dev."""
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
        requests.post(f"https://api.telegram.org/bot{token}/deleteWebhook", timeout=5)
        logger.info("Telegram webhook deleted.")
    except Exception:
        pass
