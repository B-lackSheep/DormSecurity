from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import Config

class Base(DeclarativeBase):
    pass

# Создаем асинхронный движок
engine = create_async_engine(
    Config.DB_URL.replace('postgresql://', 'postgresql+asyncpg://'),
    pool_size=5,           
    max_overflow=10,       
    pool_timeout=30,    
    pool_pre_ping=True 
)

# Создаем фабрику асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

@asynccontextmanager
async def get_async_db_session() -> AsyncSession:
    """Асинхронный контекстный менеджер для работы с БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        # Импортируем модели для создания таблиц
        from .models.db_models import Room, CleaningLog
        await conn.run_sync(Base.metadata.create_all)
