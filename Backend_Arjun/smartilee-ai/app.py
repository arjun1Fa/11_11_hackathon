import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    supabase = None
    print("Warning: SUPABASE_URL or SUPABASE_KEY not found in environment.")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    # Run the application
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
