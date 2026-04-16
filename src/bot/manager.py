import os
from pyrogram import Client, filters
from pyrogram.storage import MemoryStorage
from ..config import Config

class TelegramManager:
    def __init__(self):
        session = os.getenv("SESSION_STRING")
        if session:
            self.app = Client(
                "sb_userbot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                session_string=session
            )
        else:
            self.app = Client("sb_userbot", api_id=Config.API_ID, api_hash=Config.API_HASH)

    def setup_handlers(self, on_forecast_request):
        @self.app.on_message(filters.chat(Config.CHAT_ID) & (filters.command(["next", "очередь"]) | filters.regex(r"^\.очередь")))
        async def send_forecast(client, message):
            parts = message.text.strip().split()
            floor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            extra = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            await on_forecast_request(message, floor, extra)

    async def send_message(self, text: str):
        await self.app.send_message(Config.CHAT_ID, text)
