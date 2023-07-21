from datetime import datetime, timedelta

from sqlalchemy import and_, delete, insert, select
from sqlalchemy.sql import func

from application.auth.models import AuthToken, generate_uuid
from application.database import scoped_session
from application.users.models import User


class AuthTokenManager:
    @staticmethod
    async def create(user_id: int) -> str | None:
        async with scoped_session() as session:
            query = await session.execute(
                insert(AuthToken)
                .values(
                    key=generate_uuid(),
                    created=datetime.now() + timedelta(weeks=2),
                    user_id=user_id,
                )
                .returning(AuthToken.key)
            )
            await session.commit()
            return query.scalar()

    @staticmethod
    async def check(token: str) -> User:
        """Возвращает информацию о владельце указанного токена."""
        async with scoped_session() as session:
            query = await session.execute(
                select(User)
                .join(AuthToken, AuthToken.user_id == User.id)
                .where(and_(AuthToken.key == token, AuthToken.created > datetime.now()))
            )
            return query.scalar()

    @staticmethod
    async def delete(user_id: int) -> None:
        """Удаляет токен при выходе владельца."""
        async with scoped_session() as session:
            await session.execute(delete(AuthToken).where(AuthToken.user_id == user_id))
            await session.commit()
