import uuid
from typing import Any

import bcrypt
from asyncpg import UniqueViolationError
from sqlalchemy import and_, case, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from application.database import Base, scoped_session
from application.models import TimeStampMixin
from application.users.models import Follow, User
from application.users.schemas import Subscriptions, UserBase, UserCreate, UserOut


class UserDB:
    @staticmethod
    async def get_users(session: AsyncSession, pk: int | None) -> list[UserBase]:
        query = await session.execute(
            select(
                User.id,
                User.email,
                User.username,
                User.first_name,
                User.last_name,
                Follow.is_subscribed(pk),
                # case((and_(pk != None, Follow.user_id == pk), "True"), else_="False").label(
                #     "is_subscribed"
                # ),
            )
            .join(Follow, User.id == Follow.author_id, full=True)
            .where(User.is_active == True)
            .order_by(User.id)
        )
        return query.all()

    @staticmethod
    async def is_email(session: AsyncSession, email: str) -> int | None:
        query = await session.execute(select(User.id).where(User.email == email))
        return query.scalar()

    @staticmethod
    async def is_username(session: AsyncSession, username: str) -> int | None:
        query = await session.execute(select(User.id).where(User.username == username))
        return query.scalar()

    @staticmethod
    async def by_email(email: str) -> User | None:
        async with scoped_session() as session:
            return await session.scalar(select(User).where(User.email == email))

    @staticmethod
    async def user_by_id(session: AsyncSession, pk: int) -> UserOut:
        query = await session.execute(
            select(
                User.id,
                User.email,
                User.username,
                User.first_name,
                User.last_name,
            ).where(User.id == pk)
        )
        return query.one()

    @staticmethod
    async def user_by_id_auth(session: AsyncSession, pk: int, user_id: int) -> UserOut:
        query = await session.execute(
            select(
                User.id,
                User.email,
                User.username,
                User.first_name,
                User.last_name,
                case(
                    (and_(Follow.user_id == user_id, Follow.user_id != User.id), "True"),
                    else_="False",
                ).label("is_subscribed"),
            )
            .join(Follow, User.id == Follow.author_id, isouter=True)
            .where(User.id == pk)
        )
        return query.one()

    @staticmethod
    async def create(
        session: AsyncSession, user: UserCreate, is_staff: bool | None = False
    ) -> User:
        query = await session.execute(
            insert(User)
            .values(
                email=user.email,
                password=user.password,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=True,
                is_staff=is_staff,
                is_superuser=False,
            )
            .returning(User)
        )
        await session.commit()
        return query.one()

    @staticmethod
    async def user_active(session: AsyncSession, pk_name: int | str, is_active: bool) -> UserOut:
        query = (
            update(User)
            .values(is_active=is_active)
            .returning(
                User.id,
                User.email,
                User.username,
                User.first_name,
                User.last_name,
            )
        )

        if type(pk_name) == int:
            query = query.where(User.id == pk_name)
        else:
            query = query.where(User.name == pk_name)

        query = await session.scalar(query)
        await session.commit()
        return query

    @staticmethod
    async def update(session: AsyncSession, password: str, user_id: int) -> UserOut | None:
        try:
            user = await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(password=password)
                .returning(
                    User.id,
                    User.email,
                    User.username,
                    User.first_name,
                    User.last_name,
                )
            )
            await session.commit()
            return user.one()

        except:
            await session.rollback()
            return None

    @staticmethod
    async def delete(session: AsyncSession, pk: str) -> None:
        query = delete(User)
        if pk.isdigit():
            query = query.where(User.id == int(pk))
        else:
            query = query.where(User.name == pk)
        await session.execute(query)
        await session.commit()


class FollowDB:
    @staticmethod
    async def is_subscribed(session: AsyncSession, user_id: int, author_id: int) -> Any:
        query = await session.execute(
            select(Follow).where(Follow.user_id == user_id, Follow.author_id == author_id)
        )
        return query.fetchone()

    @staticmethod
    async def count_is_subscribed(session: AsyncSession, user_id: int) -> int:
        count = await session.execute(
            select(func.count(User.id).label("is_count"))
            .join_from(Follow, User, User.id == Follow.author_id)
            .where(Follow.user_id == user_id, User.is_active == True)
        )
        return count.one()[0] if count else 0

    @staticmethod
    async def is_subscribed_all(
        session: AsyncSession, user_id: int, page: int | None = None, limit: int | None = None
    ) -> list[Subscriptions]:
        query = (
            select(
                User.id,
                User.username,
                User.first_name,
                User.last_name,
                case((Follow.user_id == user_id, 'True'), else_='False').label("is_subscribed"),
            )
            .join_from(Follow, User, User.id == Follow.author_id)
            .where(Follow.user_id == user_id, User.is_active == True)
        )
        if limit:
            query = query.limit(limit)
            if page:
                query = query.offset((page - 1) * limit)
        query = await session.execute(query)
        return query.all()

    @staticmethod
    async def create(session: AsyncSession, user_id: int, author_id: int) -> bool:
        try:
            query = await session.execute(
                insert(Follow).values(user_id=user_id, author_id=author_id)
            )
            await session.commit()
            print(query.fetchone())
            return True
        except UniqueViolationError:
            return False

    @staticmethod
    async def delete(session: AsyncSession, user_id: int, author_id: int) -> bool | None:
        await session.execute(
            delete(Follow).where(Follow.user_id == user_id, Follow.author_id == author_id)
        )
        await session.commit()
        return True
