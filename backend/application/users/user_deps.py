from typing import Optional

from fastapi import HTTPException, status
from fastapi.param_functions import Body
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request


class OAuth2PasswordRequestForm:
    def __init__(self, email: str = Body(), password: str = Body()) -> None:
        self.email = email
        self.password = password


class OAuth2PasswordToken(OAuth2PasswordBearer):
    """
    Проверяет токен авторизованного пользователя и возвращает токен или ошибку.
    Если пользователь не авторизован выдает None для доступа неавторизованным
    пользователям.
    """

    async def __call__(self, request: Request) -> Optional[str | None]:
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        scheme, param = get_authorization_scheme_param(authorization)
        if scheme.lower() != "token":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Token"},
                )
            else:
                return None
        return param
