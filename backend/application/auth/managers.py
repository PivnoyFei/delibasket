from datetime import datetime

from sqlalchemy import and_, delete, insert, select

from application.auth.models import AuthToken, generate_uuid
from application.database import scoped_session
from application.settings import TOKEN_EXP
from application.users.models import User


class AuthTokenManager:
    async def create(self, user_id: int) -> str | None:
        """Создает токен с временем действия."""
        async with scoped_session() as session:
            query = await session.execute(
                insert(AuthToken)
                .values(
                    key=generate_uuid(),
                    created=datetime.now() + TOKEN_EXP,
                    user_id=user_id,
                )
                .returning(AuthToken.key)
            )
            await session.commit()
            return query.scalar()

    async def check(self, token: str) -> User:
        """Возвращает информацию о владельце, после проверки указанного токена."""
        async with scoped_session() as session:
            query = await session.execute(
                select(User)
                .join(AuthToken, AuthToken.user_id == User.id)
                .where(and_(AuthToken.key == token, AuthToken.created > datetime.now()))
            )
            return query.scalar()

    async def delete(self, user_id: int) -> None:
        """Удаляет все токены при выходе владельца."""
        async with scoped_session() as session:
            try:
                await session.execute(delete(AuthToken).where(AuthToken.user_id == user_id))
                await session.commit()
                return True
            except TypeError:
                return None
