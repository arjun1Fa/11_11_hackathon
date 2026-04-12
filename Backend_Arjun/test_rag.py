import os
import requests
from dotenv import load_dotenv
from supabase import create_client

# Load DB directly from .env so we can fetch users!
load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

BASE_URL = "http://127.0.0.1:5000"

def interactive_session():
    # 1. Fetch Students from the actual database
    customers = supabase.table("customers").select("name, phone_number, preferred_country").execute().data
    if not customers:
        print("❌ No customers found in database!")
        return

    print("\n" + "═"*55)
    print(" 🌍 SMARTILEE AI - DYNAMIC WHATSAPP SIMULATOR")
    print("═"*55)
    print("Choose a student from your Supabase Database to mock:\n")
    
    for i, c in enumerate(customers):
        print(f"  [{i+1}] {c['name']} (Prefers: {c.get('preferred_country', 'None')})")
        
    while True:
        choice = input("\nEnter student number (1-{}): ".format(len(customers)))
        try:
            student = customers[int(choice)-1]
            break
        except (ValueError, IndexError):
            print("⚠️ Please type a valid number.")

    phone_number = student["phone_number"]
    name = student["name"]
    
    print("\n" + "★"*55)
    print(f"📱 You are now acting as WhatsApp user: {name}")
    print(f"📞 Attached Phone: {phone_number}")
    print("💡 Type 'exit' or press CTRL+C to close the simulator.")
    print("★"*55 + "\n")

    # 2. Continuous Chat Loop
    while True:
        try:
            message = input(f"💬 [{name}] You: ")
            if message.strip().lower() in ['exit', 'quit']:
                print("Logging out...")
                break
                
            print("   🤖 AI Brain processing...")
            
            # Call Analyze API
            analyze_payload = {
                "phone_number": phone_number,
                "message_text": message
            }
            
            analyze_res = requests.post(f"{BASE_URL}/analyze", json=analyze_payload)
            if analyze_res.status_code != 200:
                print("   ❌ Analyze error:", analyze_res.text)
                continue
                
            analysis = analyze_res.json()
            print(f"   ↳ 🎯 Intent: {analysis['intent'].upper()} | 🎭 Sentiment: {analysis['sentiment'].upper()} | ⚙️ Action: {analysis['action'].upper()}")
            
            # Route logic based on Action
            action = analysis["action"]
            if action == "auto_reply":
                print("   ✍️  Generating AI RAG reply...")
                reply_payload = {
                    "phone_number": phone_number,
                    "message_text": message,
                    "intent": analysis["intent"],
                    "sentiment": analysis["sentiment"],
                    "language": analysis["language"],
                }
                reply_res = requests.post(f"{BASE_URL}/generate-reply", json=reply_payload)
                print("\n   🚀 AI COUNSELLOR REPLIES:")
                print(f"      {reply_res.json().get('reply_text', '')}")
                print("\n" + "─"*55 + "\n")

            elif action == "upsell":
                print("   🤑 Generating strategic UPSELL reply...")
                upsell_res = requests.post(f"{BASE_URL}/upsell", json=analyze_payload)
                print("\n   🚀 AI COUNSELLOR REPLIES (UPSELL):")
                print(f"      {upsell_res.json().get('upsell_message', '')}")
                print("\n" + "─"*55 + "\n")

            else:
                 print(f"\n   ⚠️  Action '{action}' chosen. AI is HOLDING response. Emitting alert to human counsellor!")
                 print("\n" + "─"*55 + "\n")

        except KeyboardInterrupt:
            print("\nSimulator closed. Goodbye!")
            break

if __name__ == "__main__":
    interactive_session()
