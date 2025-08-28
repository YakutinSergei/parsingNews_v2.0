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


async def get_123():
    async with engine_asinc.connect() as conn:
        res = await conn.execute(text("SELECT VERSION()"))
        print(f'{res.all()=}')


async_session = async_sessionmaker(engine_asinc)


class Base(DeclarativeBase):
    pass