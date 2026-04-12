"""
rag.py
RAG (Retrieval Augmented Generation) pipeline for Smartilee study abroad AI.

Responsibilities:
  1. load_knowledge_base()  — runs at Flask startup, embeds any un-embedded rows.
  2. get_embedding()        — converts text to a 1536-dim vector.
  3. retrieve_context()     — semantic search on knowledge_base, optionally
                              filtered by country and/or category.

The knowledge_base table schema (Supabase):
  id          uuid PK
  package_id  text
  country     text       (Germany | France | Netherlands)
  category    text       (overview | tuition | visa | scholarship | faq | ...)
  title       text
  content     text       (plain English — what the LLM reads)
  embedding   vector(1536)
"""

import sys
import os
from supabase import Client


# ── Embedding provider ────────────────────────────────────────────────────────
# We use the OpenAI-compatible embedding endpoint.
# With Groq: use their embedding endpoint.
# With Ollama: use nomic-embed-text locally.
# For the hackathon we default to a simple openai-compat call via the same LLM provider.

def get_embedding(text: str) -> list[float]:
    """
    Convert a text string into a 1536-dimensional vector embedding.

    Uses the OpenAI-compatible embedding endpoint from whichever provider
    is configured (Groq or Ollama). Falls back to a zero vector on failure.

    Args:
        text: The text to embed (e.g. a knowledge base row's content field).

    Returns:
        List of 1536 floats representing the vector embedding.
    """
    try:
        from openai import OpenAI

        # Always use Ollama for embeddings, regardless of the text LLM provider
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

        client = OpenAI(
            api_key="ollama",
            base_url=ollama_base_url,
        )
        model = "nomic-embed-text"

        response = client.embeddings.create(input=text, model=model)
        vector = response.data[0].embedding
        
        # Hackathon fix: Pad Ollama's 768D vector to 1536D to match the DB schema
        if len(vector) < 1536:
            vector.extend([0.0] * (1536 - len(vector)))
            
        return vector

    except Exception as e:
        print(f"[ERROR] get_embedding failed: {e}", file=sys.stderr)
        # Return a zero vector so the pipeline doesn't crash
        return [0.0] * 1536


# ── Load knowledge base at startup ───────────────────────────────────────────

def load_knowledge_base(supabase: Client) -> None:
    """
    Load all rows from the knowledge_base table.
    For any row whose embedding column is NULL, compute and store the embedding.

    Called once when Flask starts up (from app.py).

    Args:
        supabase: The initialised Supabase client from app.py.
    """
    try:
        print("[RAG] Loading knowledge base from Supabase...")

        # Fetch all rows that have no embedding yet
        resp = (
            supabase.table("knowledge_base")
            .select("id, content, embedding")
            .is_("embedding", "null")
            .execute()
        )

        rows = resp.data or []
        print(f"[RAG] Found {len(rows)} rows without embeddings. Computing now...")

        for i, row in enumerate(rows):
            content = row.get("content", "")
            if not content.strip():
                continue

            embedding = get_embedding(content)

            # Write the embedding back to Supabase
            supabase.table("knowledge_base").update(
                {"embedding": embedding}
            ).eq("id", row["id"]).execute()

            print(f"[RAG] Embedded row {i + 1}/{len(rows)}: {row['id']}")

        print("[RAG] Knowledge base ready.")

    except Exception as e:
        print(f"[ERROR] load_knowledge_base failed: {e}", file=sys.stderr)


# ── Retrieve context for a student query ──────────────────────────────────────

def retrieve_context(
    query: str,
    supabase: Client,
    top_k: int = 4,
    filter_country: str = None,
    filter_category: str = None,
) -> str:
    """
    Retrieve the most semantically relevant knowledge base rows for a query.

    Converts the query to a vector, then calls the Supabase RPC function
    match_knowledge_base() which does cosine similarity search using pgvector.

    Args:
        query:           The student's message text (or a reformulated version).
        supabase:        Initialised Supabase client.
        top_k:           Number of rows to retrieve (default 4).
        filter_country:  If provided, restrict results to this country
                         (e.g. 'Germany', 'France', 'Netherlands').
        filter_category: If provided, restrict results to this category
                         (e.g. 'visa', 'scholarship', 'tuition').

    Returns:
        A single string of the retrieved knowledge base content rows,
        separated by newlines. Ready to be injected into an LLM prompt.
        Returns an empty string if retrieval fails or no rows match.

    SQL RPC (match_knowledge_base) expected signature:
        match_knowledge_base(
            query_embedding  vector(1536),
            match_count      int,
            filter_country   text  DEFAULT NULL,
            filter_category  text  DEFAULT NULL
        )
        RETURNS TABLE (id uuid, content text, similarity float)
    """
    try:
        query_embedding = get_embedding(query)

        rpc_params = {
            "query_embedding":  query_embedding,
            "match_count":      top_k,
            "filter_country":   filter_country,
            "filter_category":  filter_category,
        }

        resp = supabase.rpc("match_knowledge_base", rpc_params).execute()
        rows = resp.data or []

        if not rows:
            print(f"[RAG] No matching rows for query (country={filter_country})", file=sys.stderr)
            return ""

        # Join content fields into a single context string for the LLM prompt
        context_parts = [row["content"] for row in rows if row.get("content")]
        return "\n\n".join(context_parts)

    except Exception as e:
        print(f"[ERROR] retrieve_context failed: {e}", file=sys.stderr)
        return ""

# ── Retrieve Chat History ─────────────────────────────────────────────────────

def get_chat_history(customer_id: str, supabase: Client) -> str:
    """
    Fetch the last 4 messages for a student and format them into a single string.
    This gives the LLM short-term conversational memory.
    """
    try:
        if not customer_id:
            return "No previous conversation history."
            
        resp = (
            supabase.table("conversations")
            .select("direction, message_text")
            .eq("customer_id", customer_id)
            .order("timestamp", desc=True)
            .limit(4)
            .execute()
        )
        
        messages = resp.data or []
        if not messages:
            return "No previous conversation history."
            
        # Reverse to chronological order (oldest -> newest)
        messages.reverse()
        
        formatted_parts = []
        for msg in messages:
            sender = "Student" if msg.get("direction") == "inbound" else "AI Counsellor"
            text = msg.get("message_text", "")
            formatted_parts.append(f"{sender}: {text}")
            
        return "\n".join(formatted_parts)
        
    except Exception as e:
        print(f"[ERROR] get_chat_history failed: {e}", file=sys.stderr)
        return "No previous conversation history."
