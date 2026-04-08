from pyrogram import Client, filters
from ..config import Config

class TelegramManager:
    def __init__(self):
        self.app = Client("sb_userbot", api_id=Config.API_ID, api_hash=Config.API_HASH)
        self.buffer = []

    def setup_handlers(self):
        @self.app.on_message(filters.chat(Config.CHAT_ID) & filters.text)
        async def catch_message(client, message):
            self.buffer.append(f"[{message.date}] {message.from_user.first_name if message.from_user else 'SBO'}: {message.text}")

    def flush_buffer(self):
        data = "\n".join(self.buffer)
        self.buffer = []
        return data

    async def send_message(self, text: str, chat_id: int = Config.CHAT_ID):
        await self.app.send_message(chat_id, text)