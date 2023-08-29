import re
from asyncio import current_task
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from redis import Redis
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, declared_attr

from application.settings import settings

ASession = AsyncGenerator[AsyncSession, None]


def resolve_table_name(name: str) -> str:
    """Resolves table names to their mapped names."""
    names = re.split("(?=[A-Z])", name)
    return "_".join([x.lower() for x in names if x])


class CustomBase:
    @declared_attr
    def __tablename__(cls) -> str:
        return resolve_table_name(cls.__name__)

    @classmethod
    def dict(cls) -> dict[str, Any]:
        return {c.name: getattr(cls, c.name) for c in cls.__table__.columns}


Base = declarative_base(cls=CustomBase)


class DatabaseSessionManager:
    def __init__(self):
        self._engine: dict[str, AsyncEngine | None] = {}
        self._sessionmaker: dict[str, async_sessionmaker | None] = {}

    def init(self, host: str, schema_name: str | None = settings.SCHEMA_NAME):
        self._engine[schema_name]: AsyncEngine = create_async_engine(host, pool_pre_ping=True)
        self._sessionmaker[schema_name]: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self._engine[schema_name],
            autocommit=False,
            class_=AsyncSession,
        )

    async def close(self, schema_name: str | None = settings.SCHEMA_NAME):
        if not self._engine.get(schema_name, None):
            raise Exception("DatabaseSessionManager is not initialized")

        await self._engine[schema_name].dispose()
        self._engine.pop(schema_name, None)
        self._sessionmaker.pop(schema_name, None)

    @asynccontextmanager
    async def connect(self, schema_name: str | None = settings.SCHEMA_NAME) -> ASession:
        if not self._engine.get(schema_name, None):
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine[schema_name].begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @asynccontextmanager
    async def scoped_session(self, schema_name: str | None = settings.SCHEMA_NAME) -> ASession:
        if not self._sessionmaker.get(schema_name, None):
            raise Exception("DatabaseSessionManager is not initialized")

        scoped_factory = async_scoped_session(
            self._sessionmaker[schema_name],
            scopefunc=current_task,
        )
        try:
            async with scoped_factory() as session:
                yield session
        except Exception:
            await scoped_factory.rollback()
            raise
        finally:
            await scoped_factory.remove()

    async def create_all(self, connection: AsyncConnection):
        await connection.run_sync(Base.metadata.create_all)

    async def drop_all(self, connection: AsyncConnection):
        await connection.run_sync(Base.metadata.drop_all)


sessionmanager = DatabaseSessionManager()
scoped_session = sessionmanager.scoped_session

db_redis: Redis = Redis.from_url(
    settings.REDIS_URL,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)
