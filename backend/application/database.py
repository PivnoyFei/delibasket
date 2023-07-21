import re
from asyncio import current_task
from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

from application.settings import settings


def resolve_table_name(name):
    """Resolves table names to their mapped names."""
    names = re.split('(?=[A-Z])', name)
    return '_'.join([x.lower() for x in names if x])


class CustomBase:
    @declared_attr
    def __tablename__(cls):
        return resolve_table_name(cls.__name__)


engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
Base = declarative_base(cls=CustomBase)
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
async_session = async_scoped_session(async_session, scopefunc=current_task)


@asynccontextmanager
async def scoped_session() -> AsyncGenerator[AsyncSession, None]:
    scoped_factory = async_scoped_session(
        async_session,
        scopefunc=current_task,
    )
    try:
        async with scoped_factory() as session:
            yield session
    finally:
        await scoped_factory.remove()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session
