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
        new_log = CleaningLog(room_id=room.id, date=parsed_date, notes=notes)
        self.db.add(new_log)
        self.db.commit()
        return new_log

    def count_rooms_on_floor(self, floor: int) -> int:
        return self.db.query(Room).filter(Room.floor == floor).count()

    def get_forecast_by_floor(self, floor: int, limit: int = 5):
        from sqlalchemy import func
        subq = (
            self.db.query(CleaningLog.room_id, func.max(CleaningLog.date).label("last_date"))
            .group_by(CleaningLog.room_id)
            .subquery()
        )
        notes_subq = (
            self.db.query(CleaningLog.room_id, CleaningLog.notes)
            .join(subq, (CleaningLog.room_id == subq.c.room_id) & (CleaningLog.date == subq.c.last_date))
            .subquery()
        )
        results = (
            self.db.query(Room, subq.c.last_date, notes_subq.c.notes)
            .outerjoin(subq, Room.id == subq.c.room_id)
            .outerjoin(notes_subq, Room.id == notes_subq.c.room_id)
            .filter(Room.floor == floor)
            .order_by(subq.c.last_date.asc().nullsfirst())
            .limit(limit)
            .all()
        )
        return results
