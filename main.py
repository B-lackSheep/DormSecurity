import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.config import Config
from src.database import get_db_session
from src.services.llm_service import LLMService
from src.services.cleaning_service import CleaningService
from src.services.daily_sync_service import DailySyncService
from src.bot.manager import TelegramManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            date_str = f"{last_date.day} {MONTHS_RU[last_date.month]}" if last_date else "ещё не дежурила"
            notes_str = f" — {notes}" if notes else ""
            response += f"{i}. Комната {room_number} (была: {date_str}){notes_str}\n"

        await message.reply(response)


async def daily_sync():
    """Ежедневная синхронизация сообщений за сегодня"""
    try:
        with get_db_session() as session:
            sync_service = DailySyncService(session)
            count = await sync_service.sync_today_messages(bot_manager)
            logger.info(f"Ежедневная синхронизация завершена успешно: {count} записей")
    except Exception as e:
        logger.error(f"Ошибка при ежедневной синхронизации: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler(timezone=Config.TZ)
    scheduler.add_job(daily_sync, 'cron', hour=Config.SYNC_HOUR, minute=Config.SYNC_MINUTE)
    scheduler.start()
    logger.info(f"Планировщик запущен: ежедневная синхронизация в {Config.SYNC_HOUR:02d}:{Config.SYNC_MINUTE:02d}")

    bot_manager.setup_handlers(on_forecast_request)
    await bot_manager.app.start()
    logger.info("Бот запущен")

    yield

    await bot_manager.app.stop()
    scheduler.shutdown()
    logger.info("Приложение остановлено")


app = FastAPI(lifespan=lifespan)


@app.get("/")
@app.head("/")
@app.post("/")
def healthcheck():
    return {"status": "ok"}


@app.post("/sync")
async def sync_history(x_token: str = Header(None)):
    if x_token != Config.SYNC_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    from src.services.admin_service import AdminService
    from src.database import get_db_session
    with get_db_session() as session:
        admin = AdminService(session)
        count = await admin.sync_history(bot_manager, limit=300)
    return {"synced": count}
