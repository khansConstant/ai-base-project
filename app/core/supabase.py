# app/core/supabase.py
from supabase import create_client, Client
import os

# --- TEMP: put your values here, move to .env later ---
from dotenv import load_dotenv

# Load .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# create client (synchronous)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
