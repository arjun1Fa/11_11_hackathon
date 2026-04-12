import requests

# Make sure your app.py is running on port 5000 in another terminal!
BASE_URL = "http://127.0.0.1:5000"

def test_my_ai(student_message: str):
    print(f"\n💬 Student says: '{student_message}'")
    print("-" * 50)

    # 1. Ask the backend to analyze the message
    print("🤖 1. Analyzing intent, sentiment, and action...")
    analyze_payload = {
        "phone_number": "+919876543210", # Doesn't matter if this doesn't exist
        "message_text": student_message
    }
    
    analyze_res = requests.post(f"{BASE_URL}/analyze", json=analyze_payload)
    if analyze_res.status_code != 200:
        print("❌ Analyze error:", analyze_res.text)
        return

    analysis = analyze_res.json()
    print("   ✅ Intent:", analysis["intent"])
    print("   ✅ Sentiment:", analysis["sentiment"])
    print("   ✅ Action Chosen:", analysis["action"])
    
    # 2. If the AI decided to auto-reply, let's see what it generated!
    action = analysis["action"]
    if action == "auto_reply":
        print("\n✍️  2. Generating RAG reply based on knowledge base...")
        
        reply_payload = {
            "phone_number": "+919876543210",
            "message_text": student_message,
            "intent": analysis["intent"],
            "sentiment": analysis["sentiment"],
            "language": analysis["language"],
        }
        reply_res = requests.post(f"{BASE_URL}/generate-reply", json=reply_payload)
        
        print("\n" + "=" * 50)
        print("🚀 FINAL REPLY SENT TO WHATSAPP:")
        print(reply_res.json().get("reply_text"))
        print("=" * 50 + "\n")

    elif action == "upsell":
        print("\n🤑  2. Generating an UPSELL reply...")
        upsell_res = requests.post(f"{BASE_URL}/upsell", json=analyze_payload)
        
        print("\n" + "=" * 50)
        print("🚀 UPSELL MESSAGE SENT TO WHATSAPP:")
        print(upsell_res.json().get("upsell_message"))
        print("=" * 50 + "\n")
        
    else:
         print(f"\n⚠️  AI chose '{action}'. Sending alert to human counsellor instead of replying!")


if __name__ == "__main__":
    # Change this question to ask anything you want!
    question = "What is the tuition fee for Germany?"
    test_my_ai(question)
