from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

import settings
from db import database
from users import schemas, user_deps
from users.models import User

db_user = User(database)
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = user_deps.OAuth2PasswordToken(
    tokenUrl="/api/auth/token/login/", scheme_name="Authorize"
)


async def get_hashed_password(password: str) -> str:
    """Хэширует пароль пользователя."""
    return password_context.hash(password)


async def verify_password(password: str, hashed_pass: str) -> bool:
    """Проверяет хэшированный пароль входящего пользователя."""
    return password_context.verify(password, hashed_pass)


async def create_access_token(email: str, expires_delta: int = None) -> str:
    """Создает access token."""
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expires_delta, "sub": str(email)}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Проверяет текущего авторизированного пользователя."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Token"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await db_user.get_user_full_by_id(token_data.sub)
    if user:
        return user
    return credentials_exception
