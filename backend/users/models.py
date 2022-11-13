from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Table, UniqueConstraint, and_, case, select)
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func

from db import Base, metadata
from users.schemas import UserCreate

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, index=True),
    Column("password", String(255)),
    Column("username", String(150), unique=True, index=True),
    Column("first_name", String(150)),
    Column("last_name", String(150)),
    Column("timestamp", DateTime(timezone=True), default=func.now()),
    Column("is_active", Boolean, default=True),
    Column("is_staff", Boolean, default=False),
    Column("is_superuser", Boolean, default=False)
)
follow = Table(
    "follows", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("author_id", Integer, ForeignKey("users.id")),
    UniqueConstraint('user_id', 'author_id', name='unique_follow')
)
authtoken_token = Table(
    "authtoken_token", metadata,
    Column(
        "key",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        unique=True,
        nullable=False,
        index=True,
    ),
    Column("created", DateTime),
    Column("user_id", Integer, ForeignKey("users.id")),
)


class Token(Base):
    async def create_token(self, user_id: int):
        return await self.database.execute(
            authtoken_token.insert()
            .values(
                key=uuid4().hex,
                created=datetime.now() + timedelta(weeks=2),
                user_id=user_id
            )
            .returning(authtoken_token.c.key)
        )

    async def check_token(self, token: UUID):
        """ Возвращает информацию о владельце указанного токена. """
        return await self.database.fetch_one(
            authtoken_token.join(users).select().where(
                and_(
                    authtoken_token.c.key == token,
                    authtoken_token.c.created > datetime.now()
                )
            )
        )

    async def delete_token(self, user_id: int):
        """ Удаляет токен при выходе владельца. """
        query = authtoken_token.delete().where(
            authtoken_token.c.user_id == user_id)
        await self.database.execute(query)


class User(Base):
    async def get_users(self, pk: int | None):
        query = (
            select([
                users,
                case(
                    [(and_(follow.c.user_id == pk, pk != None), "True")],
                    else_="False"
                )
                .label("is_subscribed")
            ])
            .join(follow, users.c.id == follow.c.author_id, full=True)
            .where(users.c.is_active == True)
            .order_by(users.c.id)
        )
        return await self.database.fetch_all(query)

    async def get_user_by_email(self, email: str) -> int | None:
        query = select(users.c.id).where(users.c.email == email)
        return await self.database.fetch_one(query)

    async def get_user_by_username(self, username: str) -> int | None:
        query = select(users.c.id).where(users.c.username == username)
        return await self.database.fetch_one(query)

    async def get_user_password_id_by_email(self, email: str):
        return await self.database.fetch_one(
            select(users.c.id, users.c.password)
            .where(users.c.email == email)
        )

    async def get_user_full_by_id(self, pk: int):
        return await self.database.fetch_one(
            select([users]).where(users.c.id == pk))

    async def get_user_full_by_id_auth(self, pk: int, user_id: int):
        query = await self.database.fetch_one(
            select(
                users.c.id,
                users.c.email,
                users.c.username,
                users.c.first_name,
                users.c.last_name,
                case([(and_(follow.c.user_id == user_id,
                       follow.c.user_id != users.c.id),
                       "True")], else_="False").label("is_subscribed")
            )
            .join(follow, users.c.id == follow.c.author_id, full=True)
            .where(users.c.id == pk)
        )
        return dict(query) if query else None

    async def create_user(self, user: UserCreate) -> int:
        return await self.database.execute(
            users.insert().values(
                email=user.email,
                password=user.password,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=True,
                is_staff=False,
                is_superuser=False
            )
        )

    async def update_user(self, password: str, user_id: int):
        await self.database.execute(
            users.update()
            .where(users.c.id == user_id)
            .values(password=password)
        )


class Follow(Base):
    async def is_subscribed(self, user_id: int, author_id: int) -> int | None:
        return await self.database.fetch_one(
            select([follow])
            .where(
                follow.c.user_id == user_id,
                follow.c.author_id == author_id
            )
        )

    async def is_subscribed_all(self, user_id: int):
        return await self.database.fetch_all(
            select(
                users.c.id,
                users.c.username,
                users.c.first_name,
                users.c.last_name,
                case([(follow.c.user_id == user_id, 'True')], else_='False')
                .label("is_subscribed")
            )
            .join_from(follow, users, users.c.id == follow.c.author_id)
            .where(follow.c.user_id == user_id, users.c.is_active == True)
        )

    async def create(self, user_id: int, author_id: int):
        query = follow.insert().values(
            user_id=user_id, author_id=author_id)
        await self.database.execute(query)

    async def delete(self, user_id: int, author_id: int):
        query = follow.delete().where(
            follow.c.user_id == user_id, follow.c.author_id == author_id)
        await self.database.execute(query)
