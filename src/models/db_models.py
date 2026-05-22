from sqlalchemy import Column, Integer, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    room_number = Column(Integer, unique=True, nullable=False)
    floor = Column(Integer)
    
    # Связь с логами уборки
    cleaning_logs = relationship("CleaningLog", back_populates="room")


class CleaningLog(Base):
    __tablename__ = 'cleaning_log'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    date = Column(Date, nullable=False)
    notes = Column(Text)
    
    # Обратная связь с комнатой
    room = relationship("Room", back_populates="cleaning_logs")
