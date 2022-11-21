from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, Response
from starlette.requests import Request

from db import database
from recipes.models import Recipe
from services import query_list
from settings import NOT_AUTHENTICATED, NOT_FOUND
from users.models import Follow, User
from users.schemas import (IsActive, ListUsers, SetPassword, SFollow,
                           Subscriptions, UserCreate, UserRegistration,
                           UserSchemas)
from users.utils import get_current_user, get_hashed_password, verify_password

router = APIRouter(prefix='/users', tags=["users"])
PROTECTED = Depends(get_current_user)
db_recipe = Recipe(database)
db_user = User(database)
db_follow = Follow(database)


@router.get("/", response_model=ListUsers)
async def users(user: User = PROTECTED):
    """ Список всех пользователей. """
    user = await db_user.get_users(user.id if user else None)
    return await query_list(user, count=len(user))


@router.post("/", response_model=UserRegistration)
async def create_user(
    user: UserCreate, is_staff: bool = False, admin: User = PROTECTED
):
    """ Администратор может создавать акаунты с правами. """
    if await db_user.get_user_by_email(user.email):
        return JSONResponse(
            {"detail": "Email already exists"},
            status.HTTP_400_BAD_REQUEST
        )
    if await db_user.get_user_by_username(user.username):
        return JSONResponse(
            {"detail": "Username already exists"},
            status.HTTP_400_BAD_REQUEST
        )
    user.password = await get_hashed_password(user.password)
    is_staff = is_staff if admin and admin.is_staff else False
    user_id = await db_user.create(user, is_staff)
    return await db_user.get_user_full_by_id(user_id)


@router.get("/me/", response_model=UserSchemas)
async def me(user: User = PROTECTED):
    """Текущий пользователь."""
    return user or NOT_AUTHENTICATED


@router.get("/subscriptions/", response_model=Subscriptions)
async def subscriptions(
    request: Request,
    page: int = None,
    limit: int = None,
    recipes_limit: int = None,
    user: User = PROTECTED
):
    """
    Мои подписки.
    Возвращает пользователей, на которых подписан текущий пользователь.
    В выдачу добавляются рецепты.
    """
    if not user:
        return NOT_AUTHENTICATED
    results = await db_follow.is_subscribed_all(user.id, page, limit)
    if results:
        results = [dict(i) for i in results]
        for user_dict in results:
            recipes = await db_recipe.check_recipe_by_id_author(
                request, author_id=user_dict["id"], limit=recipes_limit)
            user_dict["recipes"] = recipes
            user_dict["recipes_count"] = len(recipes)
        count = await db_follow.count_is_subscribed(user.id)
        return await query_list(results, request, count, page, limit)
    return Response(status_code=status.HTTP_401_UNAUTHORIZED)


@router.post("/set_password/")
@router.post("/{pk}/set_password/")
async def set_password(
    user_pas: SetPassword, pk: int = None, user: User = PROTECTED
):
    """
    Изменение пароля пользователя.
    Администратор может изменять пароль любого пользователя.
    """
    if not user:
        return NOT_AUTHENTICATED
    if user.is_staff:
        password_hashed = await get_hashed_password(user_pas.new_password)
        return await db_user.update_user(password_hashed, pk)
    if not await verify_password(user_pas.current_password, user.password):
        return JSONResponse(
            {"detail": "Incorrect password"}, status.HTTP_400_BAD_REQUEST
        )
    password_hashed = await get_hashed_password(user_pas.new_password)
    return await db_user.update_user(password_hashed, user.id)


@router.post("/{pk}/")
async def user_active(pk: str, is_active: IsActive, user: User = PROTECTED):
    """ Блокировать аккаунты пользователей может только администратор. """
    if not user:
        return NOT_AUTHENTICATED
    if user.is_staff:
        await db_user.user_active(pk, is_active)
        return db_user.get_user_full_by_id(pk)
    return Response(status_code=status.HTTP_403_FORBIDDEN)


@router.delete("/{pk}/")
async def user_delete(pk: str, user: User = PROTECTED):
    """ Удалять аккаунты пользователей может только администратор. """
    if not user:
        return NOT_AUTHENTICATED
    if user and user.is_staff:
        await db_user.delete(pk)
    return Response(status_code=status.HTTP_403_FORBIDDEN)


@router.get("/{pk}/", response_model=UserSchemas)
async def user_id(pk: int, user: User = PROTECTED):
    """Профиль пользователя. Доступно всем пользователям."""
    if user:
        user = await db_user.get_user_full_by_id_auth(pk, user.id)
    else:
        user = await db_user.get_user_full_by_id(pk)
    return user or NOT_FOUND


@router.post("/{pk}/subscribe/", response_model=SFollow)
@router.delete("/{pk}/subscribe/")
async def subscribe(request: Request, pk: int, user: User = PROTECTED):
    """ Подписка на пользователя. """
    if not user:
        return NOT_AUTHENTICATED
    if request.method == "DELETE":
        if await db_follow.delete(user.id, pk):
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        return Response(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    autor_dict = await db_user.get_user_full_by_id(pk)
    if not autor_dict:
        return NOT_FOUND
    if pk == user.id:
        return JSONResponse(
            {'errors': 'It is forbidden to unfollow or follow yourself.'},
            status.HTTP_400_BAD_REQUEST
        )
    if await db_follow.is_subscribed(user.id, pk):
        return JSONResponse(
            {'errors': 'You are already subscribed to this author.'},
            status.HTTP_400_BAD_REQUEST
        )
    await db_follow.create(user.id, pk)
    autor_dict = dict(autor_dict)
    autor_dict["is_subscribed"] = True
    recipes = await db_recipe.check_recipe_by_id_author(request, author_id=pk)
    autor_dict["recipes"] = recipes
    autor_dict["recipes_count"] = len(recipes)
    return autor_dict
