import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from sqlalchemy import URL, create_engine, text

from database.config import settings

#Не асинхроно
engine = create_engine(
    url=settings.DATADASE_URL_psycopg,
    echo=False # Что бы сыпались все запросы в консоль
)



#Асинхроно
engine_asinc = create_async_engine(
    url=settings.DATADASE_URL_asyncpg,
    echo=False  # Что бы сыпались все запросы в консоль
)



class Base(DeclarativeBase):
    pass


# фабрика сессий
async_session = sessionmaker(engine_asinc, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """
    Создаёт таблицы в БД, если их нет.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)