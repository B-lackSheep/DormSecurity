import asyncio
from src.database import get_db_session
from src.services.admin_service import AdminService
from src.bot.manager import TelegramManager


async def run_sync():
    bot = TelegramManager()

    await bot.app.start()

    print("--- Начало синхронизации истории ---")

    with get_db_session() as session:
        admin = AdminService(session)

        count = await admin.sync_history(bot, limit=120)

        print(f"--- Успех! Добавлено записей: {count} ---")

    await bot.app.stop()


if __name__ == "__main__":
    try:
        asyncio.run(run_sync())
    except Exception as e:
        print(f"Произошла ошибка: {e}")
