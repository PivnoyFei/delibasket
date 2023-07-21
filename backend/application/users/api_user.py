from typing import Any

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from application.database import get_session
from application.recipes.models import RecipeDB
from application.services import query_list
from application.settings import NOT_AUTHENTICATED, NOT_FOUND
from application.users.managers import FollowDB, UserDB
from application.users.models import User
from application.users.schemas import (
    ListUsers,
    SetPassword,
    SFollow,
    Subscriptions,
    UserCreate,
    UserOut,
    UserRegistration,
)
from application.users.utils import (
    get_current_user,
    get_hashed_password,
    verify_password,
)

router = APIRouter(prefix='/users', tags=["users"])
PROTECTED = Depends(get_current_user)
SESSION = Depends(get_session)


@router.get("/", response_model=ListUsers, status_code=status.HTTP_200_OK)
async def users(request: Request, user: User = PROTECTED, session: AsyncSession = SESSION) -> dict:
    """Список всех пользователей."""
    user_list = await UserDB.get_users(session, user.id if user else None)
    return await query_list(user_list, request, count=len(user_list))


@router.post("/", response_model=UserRegistration, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    is_staff: bool = False,
    admin: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> User | JSONResponse:
    """Администратор может создавать акаунты с правами."""
    if await UserDB.is_email(session, user.email):
        return JSONResponse({"detail": "Email already exists"}, status.HTTP_400_BAD_REQUEST)
    if await UserDB.is_username(session, user.username):
        return JSONResponse({"detail": "Username already exists"}, status.HTTP_400_BAD_REQUEST)
    user.password = await get_hashed_password(user.password)
    is_staff = is_staff if admin and admin.is_staff else False
    return await UserDB.create(session, user, is_staff)


@router.get("/me/", response_model=UserOut, status_code=status.HTTP_200_OK)
async def me(user: User = PROTECTED) -> User | JSONResponse:
    """Текущий пользователь."""
    return user or NOT_AUTHENTICATED


@router.get("/subscriptions/", response_model=Subscriptions, status_code=status.HTTP_200_OK)
async def subscriptions(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(6, ge=1),
    recipes_limit: int = Query(6, ge=1),
    recipes_page: int = Query(1, ge=1),
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> dict | JSONResponse:
    """
    Мои подписки.
    Возвращает пользователей, на которых подписан текущий пользователь.
    В выдачу добавляются рецепты.
    """
    if not user:
        return NOT_AUTHENTICATED
    result = await FollowDB.is_subscribed_all(session, user.id, page, limit)
    if result:
        result_dict = [dict(i) for i in result]

        for user_dict in result_dict:
            recipes = await RecipeDB.check_recipe_by_id_author(
                session, request, author_id=user_dict["id"], limit=recipes_limit, page=recipes_page
            )
            if recipes:
                user_dict["recipes"] = recipes
                user_dict["recipes_count"] = len(recipes)

        count = await FollowDB.count_is_subscribed(session, user.id)
        return await query_list(result_dict, request, count, page, limit)
    return NOT_FOUND


@router.post("/set_password/", response_model=UserOut, status_code=status.HTTP_200_OK)
@router.post("/{pk}/set_password/", response_model=UserOut, status_code=status.HTTP_200_OK)
async def set_password(
    user_pas: SetPassword,
    pk: int | None = None,
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> UserOut | JSONResponse:
    """
    Изменение пароля пользователя.
    Администратор может изменять пароль любого пользователя.
    """
    if not user:
        return NOT_AUTHENTICATED

    password_hashed = await get_hashed_password(user_pas.new_password)

    if user.is_staff and pk:
        if user_other := await UserDB.update(session, password_hashed, pk):
            return user_other
        return JSONResponse(
            {"detail": "An error has occurred"}, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if not await verify_password(user_pas.current_password, user.password):
        return JSONResponse({"detail": "Incorrect password"}, status.HTTP_400_BAD_REQUEST)
    if user_my := await UserDB.update(session, password_hashed, user.id):
        return user_my
    return JSONResponse({"detail": "An error has occurred"}, status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/{pk}/", response_model=UserOut, status_code=status.HTTP_200_OK)
async def user_active(
    pk: int,
    is_active: bool = Query(False),
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> UserOut | JSONResponse:
    """Блокировать аккаунты пользователей может только администратор."""
    if not user:
        return NOT_AUTHENTICATED
    if user.is_staff:
        return await UserDB.user_active(session, pk, is_active)
    return JSONResponse("No access", status_code=status.HTTP_403_FORBIDDEN)


@router.delete("/{pk}/", status_code=status.HTTP_200_OK)
async def user_delete(
    pk: str, user: User = PROTECTED, session: AsyncSession = SESSION
) -> JSONResponse:
    """Удалять аккаунты пользователей может только администратор."""
    if not user:
        return NOT_AUTHENTICATED
    if user and user.is_staff:
        await UserDB.delete(session, pk)
    return JSONResponse({"detail": "Deleted"}, status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{pk}/", response_model=UserOut, status_code=status.HTTP_200_OK)
async def user_id(
    pk: int, user: User = PROTECTED, session: AsyncSession = SESSION
) -> UserOut | JSONResponse:
    """Профиль пользователя. Доступно всем пользователям."""
    if user:
        result = await UserDB.user_by_id_auth(session, pk, user.id)
    else:
        result = await UserDB.user_by_id(session, pk)
    return result or NOT_FOUND


@router.post("/{pk}/subscribe/", response_model=SFollow)
@router.delete("/{pk}/subscribe/", status_code=status.HTTP_200_OK)
async def subscribe(
    request: Request,
    pk: int,
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> Any:
    """Подписка на пользователя."""
    if not user:
        return NOT_AUTHENTICATED
    if pk == user.id:
        return JSONResponse(
            {'errors': 'It is forbidden to unfollow or follow yourself.'},
            status.HTTP_400_BAD_REQUEST,
        )

    if request.method == "DELETE":
        if await FollowDB.delete(session, user.id, pk):
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        return Response(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    autor = await UserDB.user_by_id(session, pk)
    if not autor:
        return NOT_FOUND

    if not await FollowDB.create(session, user.id, pk):
        return JSONResponse(
            {'errors': 'You are already subscribed to this author.'}, status.HTTP_400_BAD_REQUEST
        )

    autor_dict = dict(autor)
    autor_dict["is_subscribed"] = True
    recipes = await RecipeDB.check_recipe_by_id_author(session, request, author_id=pk)
    if recipes:
        autor_dict["recipes"] = recipes
        autor_dict["recipes_count"] = len(recipes)
    return autor_dict
