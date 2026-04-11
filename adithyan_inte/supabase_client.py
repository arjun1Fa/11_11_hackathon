"""
supabase_client.py
------------------
Initializes and exposes the Supabase client as a singleton.
All other modules import `supabase` from here.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "Missing required environment variables: SUPABASE_URL and/or SUPABASE_KEY. "
        "Please set them in your .env file."
    )

# Singleton client — import this everywhere:  from supabase_client import supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
