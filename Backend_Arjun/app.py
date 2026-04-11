import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

# ── App init ────────────────────────────────────────────────────────────────
app = Flask(__name__)
# Enable CORS so the Flutter Frontend can talk to this Flask API
CORS(app)

# ── Supabase client ──────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] SUPABASE_URL and SUPABASE_KEY must be set in .env", file=sys.stderr)
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("[INFO] Supabase client connected.")

# ── LLM client ───────────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

if LLM_PROVIDER == "groq":
    llm = ChatOpenAI(
        model="llama3-70b-8192",
        openai_api_key=GROQ_API_KEY,
        openai_api_base="https://api.groq.com/openai/v1",
        temperature=0.4,
    )
    print("[INFO] LLM provider: Groq (LLaMA 3 70B)")

elif LLM_PROVIDER == "ollama":
    llm = ChatOpenAI(
        model="llama3.1",
        openai_api_key="ollama",
        openai_api_base=OLLAMA_BASE_URL,
        temperature=0.4,
    )
    print(f"[INFO] LLM provider: Ollama @ {OLLAMA_BASE_URL}")

else:
    print(f"[ERROR] Unknown LLM_PROVIDER '{LLM_PROVIDER}'. Use 'groq' or 'ollama'.", file=sys.stderr)
    sys.exit(1)

# ── RAG knowledge base preload ────────────────────────────────────────────────
from rag import load_knowledge_base
load_knowledge_base(supabase)

# ── Endpoints ────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    """Health check — confirms server is alive and which LLM provider is active."""
    return jsonify({
        "status": "ok",
        "llm_provider": LLM_PROVIDER
    }), 200


# ── Import and register all route blueprints ─────────────────────────────────
from routes.analyze import analyze_bp
from routes.generate_reply import generate_reply_bp
from routes.upsell import upsell_bp
from routes.churn import churn_bp

app.register_blueprint(analyze_bp)
app.register_blueprint(generate_reply_bp)
app.register_blueprint(upsell_bp)
app.register_blueprint(churn_bp)


# ── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    print(f"[INFO] Smartilee AI Backend starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
