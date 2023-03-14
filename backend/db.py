from asyncio import current_task
from typing import AsyncIterator

import sqlalchemy
from settings import DATABASE_URL
from sqlalchemy.ext.asyncio import (AsyncSession, async_scoped_session,
                                    create_async_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(DATABASE_URL)
Base = declarative_base()
metadata = sqlalchemy.MetaData()

async_session = async_scoped_session(
        sessionmaker(engine, expire_on_commit=False, class_=AsyncSession), scopefunc=current_task
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session
