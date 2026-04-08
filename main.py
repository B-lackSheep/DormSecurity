import logging
from apscheduler.schedulers.background import BackgroundScheduler
from src.config import Config
from src.database import get_db_session
from src.services.llm_service import LLMService
from src.services.cleaning_service import CleaningService
from src.bot.manager import TelegramManager

logging.basicConfig(level=logging.INFO)

bot_manager = TelegramManager()
llm = LLMService()


def daily_job():
    logging.info("Starting daily sync at 23:30...")
    raw_text = bot_manager.flush_buffer()
    if not raw_text:
        return

    parsed_rooms = llm.parse_daily_logs(raw_text)

    with get_db_session() as session:
        service = CleaningService(session)
        for entry in parsed_rooms:
            service.save_duty(entry['room'], entry['notes'])
    logging.info(f"Processed {len(parsed_rooms)} rooms.")


scheduler = BackgroundScheduler(timezone=Config.TZ)
scheduler.add_job(daily_job, 'cron', hour=23, minute=30)

if __name__ == "__main__":
    bot_manager.setup_handlers()
    scheduler.start()
    logging.info("Bot and Scheduler started...")
    bot_manager.app.run()
