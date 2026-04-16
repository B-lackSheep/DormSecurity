import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    DB_URL = os.getenv("DATABASE_URL")
    CHAT_ID = int(os.getenv("TARGET_CHAT_ID"))
    TZ = os.getenv("TIMEZONE", "Europe/Minsk")
    SYNC_TOKEN = os.getenv("SYNC_TOKEN", "")
    SYNC_HOUR = int(os.getenv("SYNC_HOUR", "23"))
    SYNC_MINUTE = int(os.getenv("SYNC_MINUTE", "30"))
