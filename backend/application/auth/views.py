from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from application.auth.managers import AuthTokenManager
from application.auth.permissions import IsAuthenticated, PermissionsDependency
from application.auth.schemas import TokenBase, UserLogin
from application.exceptions import BadRequestException
from application.users.managers import UserManager

router = APIRouter()


@router.post("/login/", response_model=TokenBase, status_code=HTTP_201_CREATED)
async def login(user_in: UserLogin) -> JSONResponse:
    """Получить токен авторизации.
    Используется для авторизации по емейлу и паролю, чтобы далее использовать токен при запросах."""
    user = await UserManager().by_email(user_in.email)
    if not user:
        raise BadRequestException("Неверный email")
    if not await user.check_password(user_in.password):
        raise BadRequestException("Неверный пароль")
    return JSONResponse({"auth_token": await AuthTokenManager().create(user.id)}, HTTP_201_CREATED)


@router.post(
    "/logout/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_204_NO_CONTENT,
)
async def logout(request: Request) -> Response:
    """Удаляет все токены текущего пользователя."""
    if await AuthTokenManager().delete(request.user.id):
        return Response(status_code=HTTP_204_NO_CONTENT)
