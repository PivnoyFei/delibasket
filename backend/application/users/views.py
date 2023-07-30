from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from application.auth.permissions import IsAdmin, IsAuthenticated, PermissionsDependency
from application.schemas import Result, SearchUser, SubscriptionsParams
from application.services import get_result
from application.settings import NOT_FOUND
from application.users.managers import FollowManager, UserManager
from application.users.schemas import FollowOut, SetPassword, UserCreate, UserOut

router = APIRouter()


@router.get("/", response_model=Result[UserOut], status_code=HTTP_200_OK)
async def users(request: Request, params: SearchUser = Depends()) -> Result:
    """Список пользователей."""
    count, results = await UserManager().get_all(params, request.user.id)
    return await get_result(request, count, params, results)


@router.post(
    "/",
    response_model=UserOut,
    status_code=HTTP_201_CREATED,
    response_description="Пользователь успешно создан",
)
async def create_user(user_in: UserCreate) -> UserOut:
    """Регистрация пользователя."""
    if await UserManager().is_email(user_in.email):
        return JSONResponse({"detail": "Эл. адрес уже существует"}, HTTP_400_BAD_REQUEST)
    if await UserManager().is_username(user_in.username):
        return JSONResponse({"detail": "Имя пользователя уже занято"}, HTTP_400_BAD_REQUEST)
    return await UserManager().create(user_in)


@router.get(
    "/me/",
    response_model=UserOut,
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_200_OK,
)
async def me(request: Request) -> JSONResponse:
    """Текущий пользователь."""
    return request.user


@router.get(
    "/subscriptions/",
    response_model=Result[FollowOut],
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_200_OK,
)
async def subscriptions(request: Request, params: SubscriptionsParams = Depends()) -> Result:
    """
    Мои подписки.
    Возвращает пользователей, на которых подписан текущий пользователь.
    В выдачу добавляются рецепты.
    """
    count, results = await FollowManager().is_subscribed_all(request, params)
    return await get_result(request, count, params, results)


@router.post(
    "/set_password/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_204_NO_CONTENT,
)
async def set_password(request: Request, password_in: SetPassword) -> JSONResponse:
    """
    Изменение пароля пользователя.
    Администратор может изменять пароль любого пользователя.
    """
    if await request.user.check_password(password_in.current_password):
        if await UserManager().update(password_in.new_password, request.user.id):
            return Response(status_code=HTTP_204_NO_CONTENT)

    return JSONResponse({"detail": "Неверный пароль"}, HTTP_400_BAD_REQUEST)


@router.delete(
    "/{user_id}/",
    dependencies=[Depends(PermissionsDependency([IsAdmin]))],
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_user(user_id: int) -> JSONResponse:
    """Удалять аккаунты пользователей может только администратор."""
    if await UserManager().delete(pk=user_id):
        return Response(status_code=HTTP_204_NO_CONTENT)

    return JSONResponse(
        {'errors': 'Ошибка отписки (Например, пользователь уже удален).'},
        HTTP_400_BAD_REQUEST,
    )


@router.get("/{user_id}/", response_model=UserOut, status_code=HTTP_200_OK)
async def get_user(request: Request, user_id: int) -> UserOut | JSONResponse:
    """Профиль пользователя. Доступно всем пользователям."""
    return await UserManager().by_id(user_id, request.user.id) or NOT_FOUND


@router.post(
    "/{user_id}/subscribe/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_201_CREATED,
)
async def create_subscribe(request: Request, user_id: int) -> JSONResponse:
    """Подписаться на пользователя. Доступно только авторизованным пользователям."""
    if user_id != request.user.id:
        if not await UserManager().by_id(user_id):
            return NOT_FOUND
        if await FollowManager().create(request.user.id, user_id):
            return JSONResponse({"detail": "Подписка успешно создана"}, HTTP_201_CREATED)

    return JSONResponse({'errors': 'Ошибка уже подписан.'}, HTTP_400_BAD_REQUEST)


@router.delete(
    "/{user_id}/subscribe/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_subscribe(request: Request, user_id: int) -> JSONResponse:
    """Отписаться от пользователя. Доступно только авторизованным пользователям."""
    if await FollowManager().delete(request.user.id, user_id):
        return Response(status_code=HTTP_204_NO_CONTENT)

    return JSONResponse(
        {'errors': 'Ошибка отписки (Например, если не был подписан).'},
        HTTP_400_BAD_REQUEST,
    )
