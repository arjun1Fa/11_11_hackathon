import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 1. Upsert Customer Profile
def upsert_customer(phone, name, language='en', preferred_country=None, education_level=None, field_of_study=None, ielts_score=None):
    data = {
        "phone_number": phone,
        "name": name,
        "language": language,
        "preferred_country": preferred_country,
        "education_level": education_level,
        "field_of_study": field_of_study,
        "ielts_score": ielts_score,
        "last_active": "now()"
    }
    try:
        res = supabase.table("customers").upsert(data, on_conflict="phone_number").execute()
        return res.data
    except Exception as e:
        print(f"Error upserting customer: {e}")
        return None

# 2. Get Customer Profile
def get_customer_profile(phone):
    try:
        res = supabase.table("customers").select("*").eq("phone_number", phone).single().execute()
        return res.data
    except Exception as e:
        print(f"Error fetching customer: {e}")
        return None

# 3. Log Conversation
def log_conversation(customer_id, direction, message_text, intent_label=None, sentiment=None, action_taken=None, language=None, package_context=None):
    data = {
        "customer_id": customer_id,
        "direction": direction,
        "message_text": message_text,
        "intent_label": intent_label,
        "sentiment": sentiment,
        "action_taken": action_taken,
        "language": language,
        "package_context": package_context
    }
    try:
        res = supabase.table("conversations").insert(data).execute()
        return res.data
    except Exception as e:
        print(f"Error logging conversation: {e}")
        return None

# 4. Get Conversations
def get_conversations(customer_id, limit=20):
    try:
        res = supabase.table("conversations").select("*").eq("customer_id", customer_id).order("timestamp", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        return None

# 5. Get Churn Risk Customers
def get_churn_risk_customers(threshold=0.7):
    try:
        res = supabase.table("customers").select("*").gte("churn_score", threshold).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching churn risk: {e}")
        return None

# 6. Get Dashboard Stats
def get_dashboard_stats():
    # This usually involves multiple queries or an RPC
    try:
        # Example stats
        messages_today = supabase.table("conversations").select("id", count="exact").gte("timestamp", "now() - interval '1 day'").execute()
        handoffs = supabase.table("handoff_queue").select("id", count="exact").eq("status", "pending").execute()
        
        return {
            "messages_today": messages_today.count,
            "pending_handoffs": handoffs.count
        }
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        return None

# 7. Get All Packages
def get_all_packages():
    try:
        res = supabase.table("packages").select("*").execute()
        return res.data
    except Exception as e:
        print(f"Error fetching packages: {e}")
        return None

# 8. Get Package by ID
def get_package_by_id(package_id):
    try:
        res = supabase.table("packages").select("*").eq("id", package_id).single().execute()
        return res.data
    except Exception as e:
        print(f"Error fetching package: {e}")
        return None

# 9. Get Knowledge Base Rows
def get_knowledge_base_rows():
    try:
        res = supabase.table("knowledge_base").select("*").execute()
        return res.data
    except Exception as e:
        print(f"Error fetching KB: {e}")
        return None

# 10. Update Knowledge Base Embedding
def update_knowledge_base_embedding(id, embedding):
    try:
        res = supabase.table("knowledge_base").update({"embedding": embedding}).eq("id", id).execute()
        return res.data
    except Exception as e:
        print(f"Error updating embedding: {e}")
        return None

# 11. Retrieve Context (RAG)
def retrieve_context(query_embedding, country=None, category=None, top_k=4):
    try:
        # Calls the SQL function 'match_knowledge_base'
        params = {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "filter_country": country,
            "filter_category": category
        }
        res = supabase.rpc("match_knowledge_base", params).execute()
        return res.data
    except Exception as e:
        print(f"Error retrieving context: {e}")
        return None
