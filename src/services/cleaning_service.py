from datetime import datetime
import pytz
from sqlalchemy.orm import Session
from ..models.db_models import Room, CleaningLog
from ..config import Config


class CleaningService:
    def __init__(self, db: Session):
        self.db = db

    def save_duty(self, room_number: int, notes: str):
        room = self.db.query(Room).filter(Room.room_number == room_number).first()
        if not room:
            return None

        new_log = CleaningLog(
            room_id=room.id,
            date=datetime.now(pytz.timezone(Config.TZ)).date(),
            notes=notes
        )
        self.db.add(new_log)
        self.db.commit()
        return new_log

    def get_queue(self, floor: int, limit: int = 5):
        from sqlalchemy import func
        return (self.db.query(Room.room_number)
                .outerjoin(CleaningLog)
                .filter(Room.floor == floor)
                .group_by(Room.id)
                .order_by(func.max(CleaningLog.date).asc())
                .limit(limit).all())
