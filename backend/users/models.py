import uuid
from datetime import datetime, timedelta
from typing import Any

import sqlalchemy as sa
from asyncpg import UniqueViolationError
from db import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from users.schemas import Subscriptions, UserBase, UserCreate, UserOut


def generate_uuid() -> str:
    return str(uuid.uuid4().hex)


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)
    email = sa.Column(sa.String(255), nullable=False, unique=True, index=True)
    password = sa.Column(sa.String(255), nullable=False)
    username = sa.Column(sa.String(150), nullable=False, unique=True, index=True)
    first_name = sa.Column(sa.String(150), nullable=False)
    last_name = sa.Column(sa.String(150), nullable=False)
    timestamp = sa.Column(sa.DateTime(timezone=True), nullable=False, default=func.now())
    is_active = sa.Column(sa.Boolean, nullable=False, default=True)
    is_staff = sa.Column(sa.Boolean, nullable=False, default=False)
    is_superuser = sa.Column(sa.Boolean, nullable=False, default=False)


class AuthToken(Base):
    __tablename__ = "auth_token"
    key = sa.Column(sa.String, primary_key=True, unique=True, index=True, default=generate_uuid())
    created = sa.Column(sa.DateTime())
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete='CASCADE'))


class Follow(Base):
    __tablename__ = "follows"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete='CASCADE'))
    author_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", ondelete='CASCADE'))
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'author_id'),
    )


class TokenDB:
    async def create(session: AsyncSession, user_id: int) -> str:
        query = await session.execute(
            sa.insert(AuthToken)
            .values(
                key=generate_uuid(),
                created=datetime.now() + timedelta(weeks=2),
                user_id=user_id
            )
            .returning(AuthToken.key)
        )
        await session.commit()
        return query.scalar()

    async def check(session: AsyncSession, token: str) -> User:
        """ Возвращает информацию о владельце указанного токена. """
        query = await session.execute(
            sa.select(User)
            .join(AuthToken, AuthToken.user_id == User.id)
            .where(
                sa.and_(
                    AuthToken.key == token,
                    AuthToken.created > datetime.now()
                )
            )
        )
        return query.scalar()

    async def delete(session: AsyncSession, user_id: int) -> None:
        """ Удаляет токен при выходе владельца. """
        await session.execute(sa.delete(AuthToken).where(AuthToken.user_id == user_id))
        await session.commit()


class UserDB:
    async def get_users(session: AsyncSession, pk: int | None) -> list[UserBase]:
        query = await session.execute(
            sa.select([
                User,
                sa.case(
                    [(sa.and_(Follow.user_id == pk, pk != None), "True")],
                    else_="False"
                )
                .label("is_subscribed")
            ])
            .join(Follow, User.id == Follow.author_id, full=True)
            .where(User.is_active == True)
            .order_by(User.id)
        )
        return query.scalars().all()

    async def is_email(session: AsyncSession, email: str) -> int | None:
        query = await session.execute(sa.select(User.id).where(User.email == email))
        return query.scalar()

    async def is_username(session: AsyncSession, username: str) -> int | None:
        query = await session.execute(sa.select(User.id).where(User.username == username))
        return query.scalar()

    async def get_user_password_id_by_email(session: AsyncSession, email: str) -> Any:
        query = await session.execute(
            sa.select(User.id, User.password)
            .where(User.email == email)
        )
        return query.one()

    async def user_by_id(session: AsyncSession, pk: int) -> UserOut:
        query = await session.execute(
            sa.select(
                User.id,
                User.email,
                User.username,
                User.first_name,
                User.last_name,
            ).where(User.id == pk)
        )
        return query.one()

    async def user_by_id_auth(session: AsyncSession, pk: int, user_id: int) -> UserOut:
        query = await session.execute(
            sa.select(
                User.id,
                User.email,
                User.username,
                User.first_name,
                User.last_name,
                sa.case(
                   [(sa.and_(Follow.user_id == user_id, Follow.user_id != User.id), "True")],
                   else_="False"
                ).label("is_subscribed")
            )
            .join(Follow, User.id == Follow.author_id, full=True)
            .where(User.id == pk)
        )
        return query.one()

    async def create(session: AsyncSession, user: UserCreate, is_staff: bool | None = False) -> User:
        query = await session.execute(
            sa.insert(User).values(
                email=user.email,
                password=user.password,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=True,
                is_staff=is_staff,
                is_superuser=False,
            ).returning(User)
        )
        await session.commit()
        return query.one()

    async def user_active(session: AsyncSession, pk_name: int | str, is_active: bool) -> UserOut:
        query = (
            sa.update(User)
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

    async def update(session: AsyncSession, password: str, user_id: int) -> UserOut | None:
        try:
            user = await session.execute(
                sa.update(User)
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

    async def delete(session: AsyncSession, pk: str) -> None:
        query = sa.delete(User)
        if pk.isdigit():
            query = query.where(User.id == int(pk))
        else:
            query = query.where(User.name == pk)
        await session.execute(query)
        await session.commit()


class FollowDB:
    async def is_subscribed(session: AsyncSession, user_id: int, author_id: int) -> Any:
        query = await session.execute(
            sa.select(Follow)
            .where(
                Follow.user_id == user_id,
                Follow.author_id == author_id
            )
        )
        return query.fetchone()

    async def count_is_subscribed(session: AsyncSession, user_id: int) -> int:
        count = await session.execute(
            sa.select(func.count(User.id).label("is_count"))
            .join_from(Follow, User, User.id == Follow.author_id)
            .where(Follow.user_id == user_id, User.is_active == True)
        )
        return count.one()[0] if count else 0

    async def is_subscribed_all(
        session: AsyncSession,
        user_id: int,
        page: int | None = None,
        limit: int | None = None
    ) -> list[Subscriptions]:
        query = (
            sa.select(
                User.id,
                User.username,
                User.first_name,
                User.last_name,
                sa.case([(Follow.user_id == user_id, 'True')], else_='False')
                .label("is_subscribed")
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

    async def create(session: AsyncSession, user_id: int, author_id: int) -> bool:
        try:
            query = await session.execute(
                sa.insert(Follow)
                .values(user_id=user_id, author_id=author_id)
            )
            await session.commit()
            print(query.fetchone())
            return True
        except UniqueViolationError:
            return False

    async def delete(session: AsyncSession, user_id: int, author_id: int) -> bool | None:
        await session.execute(
            sa.delete(Follow)
            .where(Follow.user_id == user_id, Follow.author_id == author_id)
        )
        await session.commit()
        return True
