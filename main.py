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


MONTHS_RU = [
    "", "января", "февраля", "марта", "апреля",
    "мая", "июня", "июля", "августа",
    "сентября", "октября", "ноября", "декабря"
]


async def on_forecast_request(message, floor: int = None, extra: int = 0):
    with get_db_session() as session:
        service = CleaningService(session)

        if floor is None:
            await message.reply("Укажите этаж, например: /очередь 3")
            return

        total_rooms = service.count_rooms_on_floor(floor)
        if total_rooms == 0:
            await message.reply(f"На {floor} этаже нет данных.")
            return

        limit = min(5 + extra, total_rooms)

        queue = service.get_forecast_by_floor(floor, limit=limit)

        response = f"Очередь на {floor} этаже ({limit} из {total_rooms}):\n"
        for i, (room_number, last_date, notes) in enumerate(queue, 1):
            if last_date:
                date_str = f"{last_date.day} {MONTHS_RU[last_date.month]}"
            else:
                date_str = "ещё не дежурила"
            notes_str = f" — {notes}" if notes else ""
            response += f"{i}. Комната {room_number} (была: {date_str}){notes_str}\n"

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
