import requests
import os
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("AI_BACKEND_URL", "").rstrip("/")
payload = {"phone_number": "919999999999", "message_text": "Hello, I need help with my application."}

print(f"\n--- TESTING TWO-HOP AI PIPELINE ---")
print(f"Base URL: {base_url}\n")

try:
    # ── STEP 1: /analyze ──
    print(f"1. Calling {base_url}/analyze ...", end=" ", flush=True)
    resp1 = requests.post(f"{base_url}/analyze", json=payload, timeout=10)
    resp1.raise_for_status()
    data1 = resp1.json()
    action = data1.get('action')
    print(f"✅ SUCCESS! (Action: {action})")
    
    # ── STEP 2: /generate-reply ──
    if action == "auto_reply" or action == "start_call":
        print(f"2. Calling {base_url}/generate-reply ...", end=" ", flush=True)
        resp2 = requests.post(f"{base_url}/generate-reply", json=payload, timeout=15)
        resp2.raise_for_status()
        data2 = resp2.json()
        reply = data2.get('reply_text') or data2.get('response')
        print(f"✅ SUCCESS!")
        print(f"\n--- FINAL AI REPLY ---\n{reply}\n")
    else:
        print(f"Step 2 skipped (Action is {action})")

    print("\n✅ PIPELINE VERIFIED!")
except Exception as e:
    print(f"\n❌ PIPELINE FAILED!")
    print(f"Error: {e}")
print(f"-----------------------------------\n")
