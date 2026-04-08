from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import Config

engine = create_engine(Config.DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    return SessionLocal()
