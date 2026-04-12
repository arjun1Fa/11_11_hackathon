import requests

# Simulate the full flow the integration engineer should do
BASE = "http://127.0.0.1:5000"

# Step 1: Analyze
analyze_resp = requests.post(f"{BASE}/analyze", json={
    "phone_number": "1094823787",
    "message_text": "I want to set an appointment tomorrow"
}, timeout=30)
print("ANALYZE response:", analyze_resp.status_code)
analyze_data = analyze_resp.json()
print("ANALYZE data:", analyze_data)

# Step 2: Generate Reply, passing the action from analyze
reply_resp = requests.post(f"{BASE}/generate-reply", json={
    "phone_number": "1094823787",
    "message_text": "I want to set an appointment tomorrow",
    "intent": analyze_data.get("intent"),
    "sentiment": analyze_data.get("sentiment"),
    "language": analyze_data.get("language"),
    "action": analyze_data.get("action")
}, timeout=30)
print("\nREPLY response:", reply_resp.status_code)
print("REPLY data:", reply_resp.json())
