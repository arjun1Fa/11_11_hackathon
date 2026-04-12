import os
from dotenv import load_dotenv
load_dotenv()
from app import supabase

resp = supabase.table("customers").update({"is_handoff_active": False, "appointment_requested": False}).neq("id", "00000000-0000-0000-0000-000000000000").execute()
print("Reset complete. Rows updated:", len(resp.data))
for r in resp.data:
    print(f"  {r['name']} ({r['phone_number']}) -> is_handoff_active={r['is_handoff_active']}")
