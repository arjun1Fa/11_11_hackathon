"""
seed_history.py
---------------
Seeds the Supabase database with realistic chat history for several types of students.
This helps the frontend engineer test the chat UI with real data.

Data:
1. Adithyan (Telegram) - Low Risk, Active.
2. Rahul (WhatsApp) - High Risk, Abandoned.
3. Priya (WhatsApp) - Medium Risk, Handed off to human.
"""

import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from supabase_client import supabase

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def seed():
    logger.info("\n═══════════════════════════════════════════════")
    logger.info("  Smartilee — Chat History Seeder")
    logger.info("═══════════════════════════════════════════════\n")

    # 1. Clear existing sample data (Optional - maybe just skip if already there)
    # logger.info("Cleaning old sample data...")

    students = [
        {
            "phone_number": "8705080509",  # Example TG ID from prev sessions
            "name": "Adithyan",
            "channel": "telegram",
            "risk_level": "low",
            "is_handoff_active": False,
            "messages": [
                ("Hello! I want to apply for MS in CS in Germany.", "inbound", -60),
                ("Hi Adithyan! That's a great choice. Germany has excellent public universities. Do you have a specific university in mind?", "outbound", -58),
                ("I am looking at TUM and RWTH Aachen.", "inbound", -55),
                ("Both are world-class! Shall I help you with the document checklist for these?", "outbound", -50)
            ]
        },
        {
            "phone_number": "919999999999", # Simulator Phone
            "name": "Rahul Verma",
            "channel": "whatsapp",
            "risk_level": "high",
            "is_handoff_active": False,
            "messages": [
                ("I'm worried about the visa process for Canada.", "inbound", -200),
                ("Visa processing for Canada can be tricky, but we have a 98% success rate. Would you like a free consultation?", "outbound", -198),
                ("Yes please, when are you free?", "inbound", -195),
                # No response for a long time -> High risk
            ]
        },
        {
            "phone_number": "918888888888",
            "name": "Priya Sharma",
            "channel": "whatsapp",
            "risk_level": "medium",
            "is_handoff_active": True,
            "messages": [
                ("Can I get a scholarship for MBA in UK?", "inbound", -30),
                ("Certainly! There are many scholarships like Chevening and GREAT. What is your GMAT score?", "outbound", -28),
                ("My score is 720.", "inbound", -25),
                ("That's an impressive score! I'm connecting you to our specialist, Ms. Anjali, who handles UK scholarships.", "outbound", -20),
                ("🙋 Connecting you to a human agent now. Please wait a moment!", "outbound", -19)
            ]
        }
    ]

    for student in students:
        phone = student["phone_number"]
        name = student["name"]
        
        # ── Step 1: Upsert Customer ───────────────────────────────────────────
        logger.info(f"Seeding student: {name} ({student['channel']})...")
        
        last_active = (datetime.now(timezone.utc) + timedelta(minutes=student["messages"][-1][2])).isoformat()
        
        customer_data = {
            "phone_number":      phone,
            "name":              name,
            "channel":           student["channel"],
            "risk_level":        student["risk_level"],
            "is_handoff_active": student["is_handoff_active"],
            "last_active":       last_active,
            "churn_score":       0.8 if student["risk_level"] == "high" else (0.4 if student["risk_level"] == "medium" else 0.1)
        }
        
        try:
            # Check if exists
            res = supabase.table("customers").select("id").eq("phone_number", phone).execute()
            if res.data:
                supabase.table("customers").update(customer_data).eq("phone_number", phone).execute()
            else:
                supabase.table("customers").insert(customer_data).execute()
        except Exception as e:
            logger.warning(f"  ⚠️  Failed to upsert customer {name}: {e}")
            continue

        # ── Step 2: Seed Messages ─────────────────────────────────────────────
        for text, direction, offset_min in student["messages"]:
            msg_time = (datetime.now(timezone.utc) + timedelta(minutes=offset_min)).isoformat()
            
            try:
                supabase.table("conversations").insert({
                    "phone_number": phone,
                    "message_text": text,
                    "direction":    direction,
                    "created_at":   msg_time
                }).execute()
            except Exception as e:
                logger.warning(f"  ⚠️  Failed to insert message for {name}: {e}")

    logger.info("\n✅ Seeding complete! Your dashboard and chat history are now ready for the frontend engineer.")

if __name__ == "__main__":
    seed()
