import uuid
from datetime import datetime, timedelta

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Table, UniqueConstraint, and_, case, select)
from sqlalchemy.sql import func

from db import Base, metadata
from users.schemas import Subscriptions, UserBase, UserCreate


def generate_uuid():
    return str(uuid.uuid4().hex)


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
    Column("user_id", Integer, ForeignKey("users.id", ondelete='CASCADE')),
    Column("author_id", Integer, ForeignKey("users.id", ondelete='CASCADE')),
    UniqueConstraint('user_id', 'author_id', name='unique_follow')
)
authtoken_token = Table(
    "authtoken_token", metadata,
    Column(
        "key",
        String,
        primary_key=True,
        default=generate_uuid(),
        unique=True,
        index=True,
    ),
    Column("created", DateTime),
    Column("user_id", Integer, ForeignKey("users.id", ondelete='CASCADE')),
)


class Token(Base):
    async def create_token(self, user_id: int):
        return await self.database.execute(
            authtoken_token.insert()
            .values(
                key=generate_uuid(),
                created=datetime.now() + timedelta(weeks=2),
                user_id=user_id
            )
            .returning(authtoken_token.c.key)
        )

    async def check_token(self, token):
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
    async def get_users(self, pk: int | None) -> list[UserBase]:
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

    async def create(self, user: UserCreate, is_staff: bool = False) -> int:
        return await self.database.execute(
            users.insert().values(
                email=user.email,
                password=user.password,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=True,
                is_staff=is_staff
            )
        )

    async def user_active(self, pk: str, is_active: bool):
        query = users.update().values(is_active=is_active)
        if pk.isdigit():
            query = query.where(users.c.id == int(pk))
        else:
            query = query.where(users.c.name == pk)
        await self.database.execute(query)

    async def update_user(self, password: str, user_id: int):
        await self.database.execute(
            users.update()
            .where(users.c.id == user_id)
            .values(password=password)
        )

    async def delete(self, pk: str):
        query = users.delete()
        if pk.isdigit():
            query = query.where(users.c.id == int(pk))
        else:
            query = query.where(users.c.name == pk)
        await self.database.execute(query)


class Follow(Base):
    async def is_subscribed(self, user_id: int, author_id: int):
        return await self.database.fetch_one(
            select([follow])
            .where(
                follow.c.user_id == user_id,
                follow.c.author_id == author_id
            )
        )

    async def count_is_subscribed(self, user_id: int) -> int:
        query = await self.database.fetch_one(
            select(func.count(users.c.id).label("is_count"))
            .join_from(follow, users, users.c.id == follow.c.author_id)
            .where(follow.c.user_id == user_id, users.c.is_active == True)
        )
        return query[0] if query else 0

    async def is_subscribed_all(
        self,
        user_id: int,
        page: int = None,
        limit: int = None
    ) -> list[Subscriptions]:
        query = (
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
        if limit:
            query = query.limit(limit)
            if page:
                query = query.offset((page - 1) * limit)
        return await self.database.fetch_all(query)

    async def create(self, user_id: int, author_id: int) -> int:
        query = follow.insert().values(
            user_id=user_id, author_id=author_id)
        await self.database.execute(query)

    async def delete(self, user_id: int, author_id: int) -> None:
        await self.database.execute(follow.delete().where(
            follow.c.user_id == user_id, follow.c.author_id == author_id)
        )
        return True
