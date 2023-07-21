from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from application.auth.managers import AuthTokenManager
from application.database import get_session
from application.settings import NOT_AUTHENTICATED
from application.users.managers import UserDB
from application.users.models import User
from application.users.schemas import TokenBase
from application.users.user_deps import OAuth2PasswordRequestForm as OAuth2
from application.users.utils import get_current_user

router = APIRouter()
PROTECTED = Depends(get_current_user)
SESSION = Depends(get_session)


@router.post("/login/", response_model=TokenBase, status_code=HTTP_200_OK)
async def login(user_in: OAuth2 = Depends()) -> JSONResponse:
    """Авторизация по емейлу и паролю, выдает токен."""
    user: User = await UserDB.by_email(user_in.email)
    if not user:
        return JSONResponse({"detail": "Неверный email"}, HTTP_400_BAD_REQUEST)
    if not await user.check_password(user_in.password):
        return JSONResponse({"detail": "Неверный пароль"}, HTTP_400_BAD_REQUEST)
    return JSONResponse({"auth_token": await AuthTokenManager.create(user.id)}, HTTP_200_OK)


@router.post("/logout/", status_code=HTTP_404_NOT_FOUND)
async def logout(user: User = PROTECTED) -> JSONResponse:
    """Удаляет все токены пользователя."""
    if not user:
        return NOT_AUTHENTICATED
    await AuthTokenManager.delete(user.id)
    return JSONResponse({"detail": "OK"})
