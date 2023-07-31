from datetime import datetime
from typing import Any

from asyncpg import UniqueViolationError
from sqlalchemy import case, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from starlette.requests import Request

from application.database import scoped_session
from application.recipes.models import Recipe
from application.schemas import SearchUser, SubscriptionsParams
from application.users.models import Follow, User
from application.users.schemas import UserCreate, UserOut


class UserManager:
    async def get_all(self, params: SearchUser, pk: int | None = None) -> tuple[int, list]:
        async with scoped_session() as session:
            count = await params.count(User)
            query = (
                select(
                    *User.list_columns("id", "email", "username", "first_name", "last_name"),
                    Follow.is_subscribed(pk),
                )
                .join(Follow, User.id == Follow.author_id, isouter=True)
                .where(User.is_active == True)
                .order_by(User.id)
            )
            count, query = [await params.search(i) for i in (count, query)]
            query = await session.execute(await params.limit_offset(query))
            return await session.scalar(count), query.all()

    async def is_email(self, email: str) -> int | None:
        async with scoped_session() as session:
            return await session.scalar(select(User.id).where(User.email == email))

    async def is_username(self, username: str) -> int | None:
        async with scoped_session() as session:
            return await session.scalar(select(User.id).where(User.username == username))

    async def by_email(self, email: str) -> User | None:
        async with scoped_session() as session:
            return await session.scalar(select(User).where(User.email == email))

    @staticmethod
    async def session_by_id(session: AsyncSession, pk: int, user_id: int | None = None) -> UserOut:
        query = await session.execute(
            select(
                *User.list_columns("id", "email", "username", "first_name", "last_name"),
                Follow.is_subscribed(pk, user_id),
            )
            .join(Follow, User.id == Follow.author_id, isouter=True)
            .where(User.id == pk)
        )
        return query.one_or_none()

    async def by_id(self, pk: int, user_id: int | None = None) -> UserOut:
        async with scoped_session() as session:
            return await self.session_by_id(session, pk, user_id)

    async def create(self, user_in: UserCreate) -> User:
        async with scoped_session() as session:
            query = await session.execute(
                insert(User).values(**user_in.model_dump()).returning(User)
            )
            await session.commit()
            return query.scalar()

    async def update(self, password: bytes, user_id: int) -> int | None:
        async with scoped_session() as session:
            try:
                user = await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(password=password, updated_at=datetime.utcnow())
                    .returning(User.id)
                )
                await session.commit()
                return user.one()

            except Exception:
                await session.rollback()
                return None

    async def delete(self, pk: int) -> bool:
        async with scoped_session() as session:
            try:
                await session.execute(delete(User).where(User.name == pk))
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                return False


class FollowManager:
    async def is_subscribed(self, session: AsyncSession, user_id: int, author_id: int) -> Any:
        query = await session.execute(
            select(Follow).where(Follow.user_id == user_id, Follow.author_id == author_id)
        )
        return query.fetchone()

    async def count_is_subscribed(self, user_id: int) -> int:
        async with scoped_session() as session:
            count = await session.execute(
                select(func.count(User.id).label("is_count"))
                .join_from(Follow, User, User.id == Follow.author_id)
                .where(Follow.user_id == user_id, User.is_active == True)
            )
            return count.one()[0] if count else 0

    @staticmethod
    async def recipe_by_author(
        session: AsyncSession,
        request: Request,
        author_id: int,
        params: SubscriptionsParams,
    ) -> list:
        query = (
            select(Recipe.id, Recipe.name, Recipe.image_path(request), Recipe.cooking_time)
            .where(Recipe.author_id == author_id)
            .order_by(Recipe.pub_date.desc(), Recipe.created_at.desc())
            .limit(params.recipes_limit)
        )
        query = await session.execute(query)
        return query.all()

    async def is_subscribed_all(
        self, request: Request, params: SubscriptionsParams
    ) -> tuple[int, list]:
        async with scoped_session() as session:
            user_id: int = request.user.id
            count = await params.count(User)
            query = select(
                *User.list_columns("id", "email", "username", "first_name", "last_name"),
                case((Follow.user_id == user_id, 'True'), else_='False').label("is_subscribed"),
            )
            count, query = [
                i.join(Follow, User.id == Follow.author_id).where(
                    Follow.user_id == user_id, User.is_active == True
                )
                for i in (count, query)
            ]
            count = await session.scalar(count)
            if not count:
                return 0, []

            query = await session.execute(await params.limit_offset(query))
            results = await params.to_dict(query.all())

            for user in results:
                recipes = await self.recipe_by_author(session, request, user["id"], params)
                if recipes:
                    user["recipes"] = recipes
                    user["recipes_count"] = len(recipes)

            return count, results

    async def create(self, user_id: int, author_id: int) -> bool:
        async with scoped_session() as session:
            try:
                await session.execute(insert(Follow).values(user_id=user_id, author_id=author_id))
                await session.commit()
                return True
            except UniqueViolationError:
                return False

    async def delete(self, user_id: int, author_id: int) -> bool | None:
        async with scoped_session() as session:
            try:
                await session.execute(
                    delete(Follow).where(Follow.user_id == user_id, Follow.author_id == author_id)
                )
                await session.commit()
                return True
            except Exception as e:
                print(f"== FollowManager == delete == {e}")
                return False
