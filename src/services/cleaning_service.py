from datetime import datetime, date
from sqlalchemy.orm import Session
from ..models.db_models import Room, CleaningLog


class CleaningService:
    def __init__(self, db: Session):
        self.db = db

    def save_duty(self, room_number: int, duty_date: str, notes: str):
        room = self.db.query(Room).filter(Room.room_number == room_number).first()
        if not room:
            return None

        parsed_date = datetime.strptime(duty_date, "%Y-%m-%d").date()

        new_log = CleaningLog(
            room_id=room.id,
            date=parsed_date,
            notes=notes
        )
        self.db.add(new_log)
        self.db.commit()
        return new_log
