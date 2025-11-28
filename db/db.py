from motor.motor_asyncio import AsyncIOMotorClient
import os
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()

try:
    client = AsyncIOMotorClient(os.getenv("DB_URI"))
    db = client["ECommerce"]
except Exception as e:
    print(f"❌ Error connecting: {e}")


# ---------- Supabase config ----------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not all([SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY]):
    raise RuntimeError("Supabase environment variables are missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)