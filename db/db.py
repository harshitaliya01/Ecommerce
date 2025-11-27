from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
load_dotenv()

try:
    client = AsyncIOMotorClient(os.getenv("DB_URI"))
    db = client["ECommerce"]
except Exception as e:
    print(f"❌ Error connecting: {e}")
