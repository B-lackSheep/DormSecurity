from datetime import datetime, date
from sqlalchemy.orm import Session
from ..models.db_models import Room, CleaningLog


class CleaningService:
    def __init__(self, db: Session):
        self.db = db

    def save_duty(self, room_number: int, duty_date: str, notes: str):
        room = self.db.query(Room).filter(Room.room_number == room_number).first()
        if not room:
            floor = int(str(room_number)[0])
            room = Room(room_number=room_number, floor=floor)
            self.db.add(room)
            self.db.flush()

        parsed_date = datetime.strptime(duty_date, "%Y-%m-%d").date()

        existing = self.db.query(CleaningLog).filter(
            CleaningLog.room_id == room.id
        ).first()

        if existing:
            if parsed_date > existing.date:
                existing.date = parsed_date
                existing.notes = notes
                self.db.commit()
            return existing

        new_log = CleaningLog(room_id=room.id, date=parsed_date, notes=notes)
        self.db.add(new_log)
        self.db.commit()
        return new_log

    def count_rooms_on_floor(self, floor: int) -> int:
        from sqlalchemy import text
        row = self.db.execute(text("""
            SELECT COUNT(DISTINCT r.id)
            FROM rooms r
            JOIN cleaning_log l ON l.room_id = r.id
            WHERE r.floor = :floor
        """), {"floor": floor}).scalar()
        return row or 0

    def get_forecast_by_floor(self, floor: int, limit: int = 5):
        from sqlalchemy import text
        rows = self.db.execute(text("""
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
        """), {"floor": floor, "limit": limit}).fetchall()
        return [(row[0], row[1], row[2]) for row in rows]
