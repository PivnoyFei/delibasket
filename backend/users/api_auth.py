from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from db import database
from settings import NOT_AUTHENTICATED
from users import schemas
from users.models import Token, User
from users.utils import get_current_user, verify_password

router = APIRouter(prefix='/auth', tags=["auth"])
PROTECTED = Depends(get_current_user)
db_user = User(database)
db_token = Token(database)


@router.post("/token/login/", response_model=schemas.TokenBase)
async def login(user: schemas.UserAuth):
    """ Авторизация по емейлу и паролю, выдает токен. """
    user = OAuth2PasswordRequestForm(
        username=user.email, password=user.password, scope="me"
    )
    user_dict = await db_user.get_user_password_id_by_email(user.username)
    if not user_dict:
        return JSONResponse(
            {"detail": "Incorrect email"}, status.HTTP_400_BAD_REQUEST
        )
    if not await verify_password(user.password, user_dict.password):
        return JSONResponse(
            {"detail": "Incorrect password"}, status.HTTP_400_BAD_REQUEST
        )
    return JSONResponse(
        {"auth_token": f"{await db_token.create_token(user_dict.id)}"},
        status.HTTP_200_OK
    )


@router.post("/token/logout/")
async def logout(user: User = PROTECTED):
    """ Удаляет все токены пользователя. """
    if not user:
        return NOT_AUTHENTICATED
    await db_token.delete_token(user.id)
