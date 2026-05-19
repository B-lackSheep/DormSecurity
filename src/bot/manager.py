import os
import logging
from ..config import Config

logger = logging.getLogger(__name__)

class TelegramManager:
    def __init__(self):
        # Отложенный импорт Pyrogram
        from pyrogram import Client, filters
        from pyrogram.storage import MemoryStorage
        
        self.Client = Client
        self.filters = filters
        
        session = os.getenv("SESSION_STRING")
        if session:
            self.app = Client(
                "sb_userbot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                session_string=session,
                ipv6=False
            )
        else:
            self.app = Client(
                "sb_userbot", 
                api_id=Config.API_ID, 
                api_hash=Config.API_HASH,
                ipv6=False
            )
        self.buffer = []

    def setup_handlers(self, on_forecast_request):
        logger.info(f"Настройка обработчиков для чата {Config.CHAT_ID}")
        
        @self.app.on_message(self.filters.chat(Config.CHAT_ID) & self.filters.text & ~self.filters.command(["next", "очередь"]))
        async def catch_message(client, message):
            self.buffer.append(f"[{message.date}] {message.text}")
            logger.debug(f"Сохранено сообщение в буфер: {message.text[:50]}...")

        @self.app.on_message(self.filters.chat(Config.CHAT_ID) & (self.filters.command(["next", "очередь"]) | self.filters.regex(r"^\.очередь")))
        async def send_forecast(client, message):
            logger.info(f"Получена команда: {message.text}")
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
