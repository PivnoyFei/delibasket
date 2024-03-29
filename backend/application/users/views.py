from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from application.auth.permissions import IsAdmin, IsAuthenticated, PermissionsDependency
from application.exceptions import BadRequestException, NotFoundException
from application.managers import Manager
from application.schemas import Result, SearchUser, SubParams
from application.users.managers import FollowManager, UserManager
from application.users.models import User
from application.users.schemas import FollowOut, SetPassword, UserCreate, UserOut

router = APIRouter()


@router.get("/", response_model=Result[UserOut], status_code=HTTP_200_OK)
async def users(request: Request, params: SearchUser = Depends()) -> dict:
    """Список пользователей."""
    count, results = await UserManager().get_all(params, request.user.id)
    return await Result.result(request.url, count, params, results)


@router.post(
    "/",
    response_model=UserOut,
    status_code=HTTP_201_CREATED,
    response_description="Пользователь успешно создан",
)
async def create_user(user_in: UserCreate) -> UserOut:
    """Регистрация пользователя."""
    if await UserManager().is_email(user_in.email):
        raise BadRequestException("Эл. адрес уже существует")
    if await UserManager().is_username(user_in.username):
        raise BadRequestException("Имя пользователя уже занято")
    return await UserManager().create(user_in)


@router.get(
    "/me/",
    response_model=UserOut,
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_200_OK,
)
async def me(request: Request) -> JSONResponse:
    """Текущий пользователь."""
    return await Manager(User).by_id(request.user.id)


@router.get(
    "/subscriptions/",
    response_model=Result[FollowOut],
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_200_OK,
)
async def subscriptions(request: Request, params: SubParams = Depends()) -> dict:
    """Мои подписки.<br>
    Возвращает пользователей, на которых подписан текущий пользователь.<br>
    В выдачу добавляются рецепты."""
    count, results = await FollowManager().is_subscribed(request, params)
    return await Result.result(request.url, count, params, results)


@router.post(
    "/set_password/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_204_NO_CONTENT,
)
async def set_password(request: Request, password_in: SetPassword) -> JSONResponse:
    """Изменение пароля пользователя.<br>
    Администратор может изменять пароль любого пользователя."""
    user: User = await Manager(User).by_id(request.user.id)
    if user.check_password(password_in.current_password):
        if await UserManager().update(password_in.new_password, request.user.id):
            return Response(status_code=HTTP_204_NO_CONTENT)

    raise BadRequestException("Неверный пароль")


@router.delete(
    "/{user_id}/",
    dependencies=[Depends(PermissionsDependency([IsAdmin]))],
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_user(user_id: int) -> JSONResponse:
    """Удалять аккаунты пользователей может только администратор."""
    if await UserManager().delete(pk=user_id):
        return Response(status_code=HTTP_204_NO_CONTENT)

    raise BadRequestException("Ошибка отписки (Например, пользователь уже удален).")


@router.get("/{user_id}/", response_model=UserOut, status_code=HTTP_200_OK)
async def get_user(request: Request, user_id: int) -> UserOut | JSONResponse:
    """Профиль пользователя. Доступно всем пользователям."""
    if result := await UserManager().by_id(user_id, request.user.id):
        return result
    raise NotFoundException


@router.post(
    "/{user_id}/subscribe/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_201_CREATED,
)
async def create_subscribe(request: Request, user_id: int) -> JSONResponse:
    """Подписаться на пользователя. Доступно только авторизованным пользователям."""
    if user_id != request.user.id:
        if not await UserManager().by_id(user_id, request.user.id):
            raise NotFoundException
        if await FollowManager().create(user_id, request.user.id):
            return JSONResponse({"detail": "Подписка успешно создана"}, HTTP_201_CREATED)

    raise BadRequestException("Ошибка уже подписан.")


@router.delete(
    "/{user_id}/subscribe/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_subscribe(request: Request, user_id: int) -> JSONResponse:
    """Отписаться от пользователя. Доступно только авторизованным пользователям."""
    if await FollowManager().delete(user_id, request.user.id):
        return Response(status_code=HTTP_204_NO_CONTENT)

    raise BadRequestException("Ошибка отписки (Например, если не был подписан).")
