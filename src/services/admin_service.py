import re
import time
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

    async def sync_history(self, bot_manager, limit: int = 195):
        messages = []
        async for msg in bot_manager.app.get_chat_history(Config.CHAT_ID, limit=limit):
            if not msg.text:
                continue
            text = msg.text.strip()
            if text.startswith('/') or text.startswith('.'):
                continue
            if text.startswith('Очередь на '):
                continue
            date_str = msg.date.strftime('%Y-%m-%d %H:%M:%S')
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith('Очередь на '):
                    continue
                if re.match(r'^\d+\.\s', line) and 'была:' in line:
                    continue
                messages.append(f"[{date_str}] {line}")

        if not messages:
            print("Сообщений в чате не найдено.")
            return 0

        print(f"Найдено сообщений о дежурствах: {len(messages)}, отправляю в LLM батчами...")

        llm = LLMService()
        service = CleaningService(self.db)
        batch_size = 15
        count = 0

        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            parsed = llm.parse_logs_with_dates("\n".join(batch))
            if not parsed:
                print(f"Батч {i // batch_size + 1}: LLM не нашёл дежурств или ошибка")
                continue
            batch_count = 0
            for entry in parsed:
                result = service.save_duty(entry['room'], entry['date'], entry['notes'])
                if result and result['action'] in ['created', 'updated']:
                    count += 1
                    batch_count += 1
            print(f"Батч {i // batch_size + 1}: LLM нашёл {len(parsed)}, сохранено/обновлено {batch_count}")
            time.sleep(3)

        return count
