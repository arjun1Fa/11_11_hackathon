import os
from dotenv import load_dotenv
load_dotenv()

from app import supabase
from rag import retrieve_context

# 1. Check knowledge base contents
resp = supabase.table("knowledge_base").select("id, country, category, title, embedding").execute()
rows = resp.data or []
print(f"Total knowledge base rows: {len(rows)}")
for r in rows:
    has_emb = r.get("embedding") is not None
    print(f"  country={r.get('country')} | category={r.get('category')} | has_embedding={has_emb} | title={str(r.get('title',''))[:50]}")

# 2. Try a direct search for Germany
print("\n--- Testing retrieve_context for Germany ---")
result = retrieve_context("What are the opportunities in Germany for CS students?", supabase, filter_country="Germany")
if result:
    print("RAG Result (first 500 chars):", result[:500])
else:
    print("RAG returned EMPTY for Germany")

# 3. Try without country filter
print("\n--- Testing retrieve_context WITHOUT country filter ---")
result2 = retrieve_context("What are the opportunities in Germany for CS students?", supabase)
if result2:
    print("RAG Result (no filter, first 500 chars):", result2[:500])
else:
    print("RAG returned EMPTY without filter too")
