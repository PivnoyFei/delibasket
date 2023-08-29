from uuid import uuid4

from application.auth.schemas import CurrentUser
from application.database import db_redis
from application.settings import settings


def generate_uuid() -> str:
    return str(uuid4().hex)


class AuthTokenRedisManager:
    async def create(self, user: CurrentUser) -> str | None:
        """Создает токен с временем действия."""
        token = generate_uuid()
        db_redis.hset(
            token,
            mapping={
                "id": user.id,
                "username": user.username,
                "is_active": int(user.is_active),
                "is_staff": int(user.is_staff),
                "is_superuser": int(user.is_superuser),
            },
        )
        db_redis.expire(token, settings.TOKEN_EXP)
        return token

    async def check(self, token: str) -> CurrentUser | None:
        """Возвращает информацию о владельце, после проверки указанного токена."""
        if items := db_redis.hgetall(token):
            return CurrentUser(**items)

    async def delete(self, token: str) -> bool:
        """Удаляет все токены при выходе владельца."""
        db_redis.delete(token)
