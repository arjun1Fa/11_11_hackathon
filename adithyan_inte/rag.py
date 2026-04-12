"""
rag.py
------
RAG pipeline for Smartilee Study Abroad vertical.
Handles embedding generation and retrieval from Supabase knowledge_base.
"""

import os
import logging
from typing import List, Optional
from supabase_client import supabase

logger = logging.getLogger(__name__)

# Configuration
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq") # groq or ollama
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

def get_embedding(text: str) -> List[float]:
    """
    Generates a vector embedding for the given text.
    In a real implementation, this would call Groq, Ollama, or OpenAI.
    Here we provide a stub that matches the VECTOR(1536) requirement.
    """
    # NOTE: To use real embeddings, integrate with ChatOpenAI or similar.
    # For now, we return a mock vector to satisfy the DB schema.
    import random
    return [random.uniform(-1, 1) for _ in range(1536)]

def load_knowledge_base():
    """
    Utility to initialize the knowledge base embeddings.
    Reads all rows from knowledge_base; if embedding is null, generates one.
    """
    logger.info("Initializing knowledge base embeddings...")
    try:
        result = supabase.table("knowledge_base").select("*").is_("embedding", "null").execute()
        rows = result.data or []
        
        for row in rows:
            embedding = get_embedding(row["content"])
            supabase.table("knowledge_base").update({"embedding": embedding}).eq("id", row["id"]).execute()
            logger.info("Generated embedding for row %s", row["id"])
            
    except Exception as exc:
        logger.error("Failed to load knowledge base: %s", exc)

def retrieve_context(query: str, top_k: int = 4, filter_country: Optional[str] = None, filter_category: Optional[str] = None) -> str:
    """
    Converts query to vector and performs semantic search using match_knowledge_base RPC.
    """
    query_embedding = get_embedding(query)
    
    try:
        rpc_params = {
            "query_embedding": query_embedding,
            "match_limit": top_k,
            "filter_country": filter_country,
            "filter_category": filter_category
        }
        
        result = supabase.rpc("match_knowledge_base", rpc_params).execute()
        matches = result.data or []
        
        if not matches:
            return ""
            
        context_parts = []
        for m in matches:
            context_parts.append(f"[{m['country']} - {m['category']}] {m['content']}")
            
        return "\n\n".join(context_parts)
        
    except Exception as exc:
        logger.error("RAG context retrieval failed: %s", exc)
        return ""
