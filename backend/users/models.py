from databases import Database
from sqlalchemy import Column, ForeignKey, DateTime, Integer, String, Table, UniqueConstraint, Boolean, select, case, literal_column, text, join
from sqlalchemy.sql import func

from db import metadata
from users.schemas import UserCreate, Userfull, UserAuth, ListUserfull

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


class User:
    def __init__(self, database: Database):
        self.database = database

    async def get_users_all(self, pk: int):
        query = (
            select(
                users.c.id,
                users.c.email,
                users.c.username,
                users.c.first_name,
                users.c.last_name,
                case([(follow.c.user_id == pk, 'True')], else_='False')
                .label("is_subscribed")
            )
            .join_from(follow, users, users.c.id == follow.c.author_id, full=True)
            .where(users.c.is_active == True)
            .order_by(users.c.id)
        )
        query = await self.database.fetch_all(query)
        print("=== query 2 ===", query)
        return query

    async def get_user_by_email(self, email: str) -> int | None:
        query = select(users.c.id).where(users.c.email == email)
        return await self.database.fetch_one(query)

    async def get_user_by_username(self, username: str) -> int | None:
        query = select(users.c.id).where(users.c.username == username)
        return await self.database.fetch_one(query)

    async def get_user_password_id_by_email(self, email: str) -> UserAuth | None:
        query = select(users.c.id, users.c.password).where(
            users.c.email == email, users.c.is_active == True)
        return await self.database.fetch_one(query)

    async def get_user_full_by_id(self, pk: int):
        query = select([users]).where(users.c.id == pk, users.c.is_active == True)
        return dict(await self.database.fetch_one(query))

        #"id": 1,
        #"email": "kekki@fake.fake",
        #"username": "kekki",
        #"first_name": "kekki",
        #"last_name": "kekki",
        #"is_subscribed": false

    async def create_user(self, user: UserCreate):
        query = users.insert().values(
            email=user.email,
            password=user.password,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=True,
            is_staff=False,
            is_superuser=False
        )
        return await self.database.execute(query)

    async def update_user(
        self, first_name: str, last_name: str, email: str, id: int
    ):
        query = users.update().where(users.c.id == id).values(
            first_name=first_name, last_name=last_name, email=email)
        await self.database.execute(query)


class Follow:
    def __init__(self, database: Database):
        self.database = database

    async def is_subscribed(self, user_id: int, author_id: int) -> int | None:
        query = select([follow]).where(
            follow.c.user_id == user_id, follow.c.author_id == author_id
        )
        return await self.database.fetch_one(query)

    async def is_subscribed_all(self, user_id: int):
        query = (
            select(
                users.c.id,
                users.c.email,
                users.c.username,
                users.c.first_name,
                users.c.last_name,
                case([(follow.c.user_id == user_id, 'True')], else_='False')
                .label("is_subscribed")
            )
            .join_from(follow, users, users.c.id == follow.c.author_id)
            .where(follow.c.user_id == user_id, users.c.is_active == True)
        )
        print("=== query ===", query)
        return await self.database.fetch_all(query)

    async def create(self, user_id: int, author_id: int):
        query = follow.insert().values(user_id=user_id, author_id=author_id)
        await self.database.execute(query)

    async def delete(self, user_id: int, author_id: int):
        query = follow.delete().where(
            follow.c.user_id == user_id, follow.c.author_id == author_id
        )
        await self.database.execute(query)