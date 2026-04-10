from sqlalchemy import Column, Integer, Date, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    room_number = Column(Integer, unique=True, nullable=False)
    floor = Column(Integer)


class CleaningLog(Base):
    __tablename__ = 'cleaning_log'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    date = Column(Date, nullable=False)
    notes = Column(Text)
