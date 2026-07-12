from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from sqlalchemy.orm import selectinload
from ..models.db_models import Room, CleaningLog


class CleaningService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_duty(self, room_number: int, duty_date: str, notes: str):
        # Поиск комнаты
        stmt = select(Room).where(Room.room_number == room_number)
        result = await self.db.execute(stmt)
        room = result.scalar_one_or_none()

        if not room:
            floor = int(str(room_number)[0])
            room = Room(room_number=room_number, floor=floor)
            self.db.add(room)
            await self.db.flush()

        parsed_date = datetime.strptime(duty_date, "%Y-%m-%d").date()

        # Поиск существующей записи
        stmt = select(CleaningLog).where(CleaningLog.room_id == room.id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        # Очищаем входящую заметку от пробелов для надежной проверки
        clean_notes = notes.strip() if notes else ""

        if existing:
            if parsed_date > existing.date:
                old_date = existing.date
                existing.date = parsed_date

                if clean_notes:
                    existing.notes = clean_notes

                await self.db.commit()
                return {"action": "updated", "room": room_number, "old_date": old_date, "new_date": parsed_date,
                        "notes": existing.notes}

            elif parsed_date == existing.date:
                if clean_notes and existing.notes != clean_notes:
                    old_notes = existing.notes
                    existing.notes = clean_notes
                    await self.db.commit()
                    return {"action": "notes_updated", "room": room_number, "date": parsed_date, "old_notes": old_notes,
                            "new_notes": clean_notes}
                else:
                    return {"action": "skipped", "room": room_number, "date": existing.date,
                            "reason": "same_date_no_new_notes"}
            else:
                reason = "older_date"
                return {"action": "skipped", "room": room_number, "date": existing.date, "reason": reason}

        new_log = CleaningLog(room_id=room.id, date=parsed_date, notes=clean_notes)
        self.db.add(new_log)
        await self.db.commit()
        return {"action": "created", "room": room_number, "date": parsed_date, "notes": clean_notes}

    async def count_rooms_on_floor(self, floor: int) -> int:
        stmt = text("""
            SELECT COUNT(DISTINCT r.id)
            FROM rooms r
            JOIN cleaning_log l ON l.room_id = r.id
            WHERE r.floor = :floor
        """)
        result = await self.db.execute(stmt, {"floor": floor})
        row = result.scalar()
        return row or 0

    async def get_forecast_by_floor(self, floor: int, limit: int = 5):
        stmt = text("""
            SELECT r.room_number, MAX(l.date) AS last_date,
                   (SELECT l2.notes FROM cleaning_log l2
                    WHERE l2.room_id = r.id
                    ORDER BY l2.date DESC LIMIT 1) AS notes
            FROM rooms r
            JOIN cleaning_log l ON l.room_id = r.id
            WHERE r.floor = :floor
            GROUP BY r.id, r.room_number
            ORDER BY last_date ASC
            LIMIT :limit
        """)
        result = await self.db.execute(stmt, {"floor": floor, "limit": limit})
        rows = result.fetchall()
        return [(row[0], row[1], row[2]) for row in rows]