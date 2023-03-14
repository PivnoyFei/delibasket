from db import get_session
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from users.models import TokenDB, User
from users.schemas import UserOut
from users.user_deps import OAuth2PasswordToken

SESSION = Depends(get_session)
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordToken(
    tokenUrl="/api/auth/token/login/", scheme_name="Authorize"
)


async def get_hashed_password(password: str) -> str:
    """Хэширует пароль пользователя."""
    return password_context.hash(password)


async def verify_password(password: str, hashed_pass: str) -> bool:
    """Проверяет хэшированный пароль пользователя."""
    return password_context.verify(password, hashed_pass)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme), session: AsyncSession = SESSION
) -> UserOut | None:
    """Проверяет текущего авторизированного пользователя."""
    if not token:
        return None

    user: User = await TokenDB.check(session, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Token"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return user
