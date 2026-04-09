from datetime import date
from sqlalchemy.orm import Session
from ..models.db_models import Room, CleaningLog
from .llm_service import LLMService
from .cleaning_service import CleaningService
from ..config import Config


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def update_room_date(self, room_number: int, new_date: date):
        room = self.db.query(Room).filter(Room.room_number == room_number).first()
        if not room: return "Комната не найдена"

        last_log = self.db.query(CleaningLog).filter(CleaningLog.room_id == room.id).order_by(
            CleaningLog.date.desc()).first()
        if last_log:
            last_log.date = new_date
        else:
            last_log = CleaningLog(room_id=room.id, date=new_date, notes="Ручная корректировка")
            self.db.add(last_log)

        self.db.commit()
        return f"Обновлено: {room_number} теперь имеет дату {new_date}"

    async def sync_history(self, bot_manager, limit: int = 100):
        messages = []
        async for msg in bot_manager.app.get_chat_history(Config.CHAT_ID, limit=limit):
            if msg.text:
                messages.append(f"[{msg.date}] {msg.text}")

        if not messages:
            print("Сообщений в чате не найдено.")
            return 0

        parsed = LLMService().parse_logs_with_dates("\n".join(messages))
        service = CleaningService(self.db)
        count = 0
        for entry in parsed:
            if service.save_duty(entry['room'], entry['date'], entry['notes']):
                count += 1
        return count
