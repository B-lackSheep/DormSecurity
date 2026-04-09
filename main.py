import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from src.config import Config
from src.database import get_db_session
from src.services.llm_service import LLMService
from src.services.cleaning_service import CleaningService
from src.bot.manager import TelegramManager

logging.basicConfig(level=logging.INFO)

bot_manager = TelegramManager()
llm = LLMService()


async def on_forecast_request(message):
    with get_db_session() as session:
        service = CleaningService(session)
        queue = service.get_forecast(limit=5)

        if not queue:
            await message.reply("База данных пока пуста.")
            return

        response = "Прогноз следующих дежурных:\n"
        for i, (room, last_date) in enumerate(queue, 1):
            date_str = last_date.strftime("%d.%m.%Y") if last_date else "еще не дежурила"
            response += f"{i}. **Комната {room}** (была: {date_str})\n"

        await message.reply(response)


def daily_sync():
    raw_text = bot_manager.flush_buffer()
    if not raw_text: return

    parsed_rooms = llm.parse_logs_with_dates(raw_text)

    with get_db_session() as session:
        service = CleaningService(session)
        for entry in parsed_rooms:
            service.save_duty(entry['room'], entry['date'], entry['notes'])
    logging.info(f"Daily sync completed: {len(parsed_rooms)} rooms saved.")


scheduler = BackgroundScheduler(timezone=Config.TZ)
scheduler.add_job(daily_sync, 'cron', hour=23, minute=30)

if __name__ == "__main__":
    bot_manager.setup_handlers(on_forecast_request)
    scheduler.start()
    logging.info("Bot started in demand-only mode.")
    bot_manager.app.run()
