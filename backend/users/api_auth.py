from db import get_session
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from settings import NOT_AUTHENTICATED
from sqlalchemy.ext.asyncio import AsyncSession
from users.models import TokenDB, User, UserDB
from users.schemas import TokenBase
from users.user_deps import OAuth2PasswordRequestForm as OAuth2
from users.utils import get_current_user, verify_password

router = APIRouter(prefix='/auth', tags=["auth"])
PROTECTED = Depends(get_current_user)
SESSION = Depends(get_session)


@router.post("/token/login/", response_model=TokenBase, status_code=status.HTTP_200_OK)
async def login(user: OAuth2 = Depends(), session: AsyncSession = SESSION) -> JSONResponse:
    """ Авторизация по емейлу и паролю, выдает токен. """
    user_dict = await UserDB.get_user_password_id_by_email(session, user.email)
    if not user_dict:
        return JSONResponse(
            {"detail": "Incorrect email"}, status.HTTP_400_BAD_REQUEST
        )
    if not await verify_password(user.password, user_dict.password):
        return JSONResponse(
            {"detail": "Incorrect password"}, status.HTTP_400_BAD_REQUEST
        )
    return JSONResponse(
        {"auth_token": await TokenDB.create(session, user_dict.id)},
        status.HTTP_200_OK
    )


@router.post("/token/logout/", status_code=status.HTTP_404_NOT_FOUND)
async def logout(user: User = PROTECTED, session: AsyncSession = SESSION) -> JSONResponse:
    """ Удаляет все токены пользователя. """
    if not user:
        return NOT_AUTHENTICATED
    await TokenDB.delete(session, user.id)
    return JSONResponse({"detail": "OK"})
