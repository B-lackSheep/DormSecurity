import asyncio
from pyrogram import Client
from src.config import Config

async def get_session():
    app = Client("session", api_id=Config.API_ID, api_hash=Config.API_HASH)
    await app.start()
    session_string = await app.export_session_string()
    print(f"SESSION_STRING={session_string}")
    await app.stop()

asyncio.run(get_session())
