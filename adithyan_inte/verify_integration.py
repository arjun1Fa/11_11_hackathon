"""
verify_integration.py
---------------------
Diagnostic script to test the Smartilee Integration Layer locally.
Run this while your Flask server (app.py) is running on port 5000.
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:5000"
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "smartilee_verify_2024")

def test_webhook_verification():
    """Simulates Meta's GET /webhook verification challenge."""
    print("\n[1/3] Testing Webhook Verification (GET)...")
    challenge = "challenge_123"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": VERIFY_TOKEN,
        "hub.challenge": challenge
    }
    try:
        response = requests.get(f"{BASE_URL}/webhook", params=params)
        if response.status_code == 200 and response.text == challenge:
            print("✅ SUCCESS: Webhook verification handshake working.")
        else:
            print(f"❌ FAILED: Received status {response.status_code}, response: '{response.text}'")
    except Exception as exc:
        print(f"❌ ERROR: Connection failed: {exc}")

def test_inbound_message():
    """Simulates Meta's POST /webhook message delivery."""
    print("\n[2/3] Testing Inbound Message (POST)...")
    
    # Sample Meta JSON payload
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456789",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "12345", "phone_number_id": "12345"},
                    "contacts": [{"profile": {"name": "Test User"}, "wa_id": "919876543210"}],
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.HBgLOTExOTg3NjU0MzIxMBUCABEYRjk2QzU5Qzk5Q0Y0MkQ3MTU4AA==",
                        "timestamp": "1718000000",
                        "text": {"body": "I want to study in Germany"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/webhook", json=payload)
        if response.status_code == 200:
            print("✅ SUCCESS: Webhook accepted the message.")
            print("   Check your Flask console logs to see if it forwarded to the AI backend!")
        else:
            print(f"❌ FAILED: Received status {response.status_code}")
    except Exception as exc:
        print(f"❌ ERROR: Connection failed: {exc}")

def test_health():
    """Simple check for server status."""
    print("\n[3/3] Checking Server Health (GET)...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"✅ SUCCESS: Server health data: {response.json()}")
        else:
            print(f"❌ FAILED: Received status {response.status_code}")
    except Exception as exc:
        print(f"❌ ERROR: Connection failed: {exc}")

if __name__ == "__main__":
    print("-" * 40)
    print(" Smartilee Integration Diagnostic Tool")
    print("-" * 40)
    test_health()
    test_webhook_verification()
    test_inbound_message()
    print("-" * 40)
    print("\n💡 Tip: Make sure 'python app.py' is running before starting this script.")
