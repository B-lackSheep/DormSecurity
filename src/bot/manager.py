from pyrogram import Client, filters
from ..config import Config

class TelegramManager:
    def __init__(self):
        self.app = Client("sb_userbot", api_id=Config.API_ID, api_hash=Config.API_HASH)
        self.buffer = []

    def setup_handlers(self, on_forecast_request):
        @self.app.on_message(filters.chat(Config.CHAT_ID) & filters.text & ~filters.command(["next", "очередь"]))
        async def catch_message(client, message):
            self.buffer.append(f"[{message.date}] {message.text}")

        @self.app.on_message(filters.chat(Config.CHAT_ID) & (filters.command(["next", "очередь"]) | filters.regex(r"^\.очередь")))
        async def send_forecast(client, message):
            parts = message.text.strip().split()
            floor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            extra = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            await on_forecast_request(message, floor, extra)

    def flush_buffer(self):
        data = "\n".join(self.buffer)
        self.buffer = []
        return data

    async def send_message(self, text: str):
        await self.app.send_message(Config.CHAT_ID, text)
