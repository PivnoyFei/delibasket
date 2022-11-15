from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, Response
from starlette.requests import Request

from db import database
from recipes.models import Recipe
from services import query_list
from settings import NOT_AUTHENTICATED, NOT_FOUND
from users import schemas
from users.models import Follow, User
from users.utils import get_current_user, get_hashed_password, verify_password

router = APIRouter(prefix='/users', tags=["users"])
db_recipe = Recipe(database)
db_user = User(database)
db_follow = Follow(database)


@router.get("/", response_model=schemas.ListUsers)
async def users(user: User = Depends(get_current_user)):
    """Список пользователей."""
    user = await db_user.get_users(user.id if user else None)
    return await query_list(user)


@router.post("/", response_model=schemas.UserRegistration)
async def create_user(user: schemas.UserCreate):
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
    user_id = await db_user.create_user(user)
    return await db_user.get_user_full_by_id(user_id)


@router.get("/me/", response_model=schemas.UserSchemas)
async def me(user: User = Depends(get_current_user)):
    """Текущий пользователь."""
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name
    } or NOT_AUTHENTICATED


@router.get("/subscriptions/", response_model=schemas.Subscriptions)
async def subscriptions(
    request: Request, user: User = Depends(get_current_user)
):
    """
    Мои подписки.
    Возвращает пользователей, на которых подписан текущий пользователь.
    В выдачу добавляются рецепты.
    """
    if not user:
        return NOT_AUTHENTICATED
    results = await db_follow.is_subscribed_all(user.id)
    if results:
        results = [dict(i) for i in results]
        for user_dict in results:
            recipes = await db_recipe.check_recipe_by_id_author(
                request, author_id=user_dict["id"])
            user_dict["recipes"] = recipes
            user_dict["recipes_count"] = len(recipes)
        return await query_list(results)
    return Response(status_code=status.HTTP_401_UNAUTHORIZED)


@router.post("/set_password/")
async def set_password(
    user_pas: schemas.SetPassword, user: User = Depends(get_current_user)
):
    if not user:
        return NOT_AUTHENTICATED
    if not await verify_password(user_pas.pas_old, user.password):
        return JSONResponse("Incorrect password", status.HTTP_400_BAD_REQUEST)
    password_hashed = await get_hashed_password(user_pas.pas_two)
    return await db_user.update_user(password_hashed, user.id)


@router.get("/{pk}/", response_model=schemas.UserSchemas)
async def user_id(pk: int, user: User = Depends(get_current_user)):
    """Профиль пользователя. Доступно всем пользователям."""
    if user:
        user = await db_user.get_user_full_by_id_auth(pk, user.id)
    else:
        user = await db_user.get_user_full_by_id(pk)
    return user or NOT_FOUND


@router.post("/{pk}/subscribe/", response_model=schemas.Follow)
async def create_subscribe(
    request: Request, pk: int, user: User = Depends(get_current_user)
):
    if not user:
        return NOT_AUTHENTICATED

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


@router.delete("/{pk}/subscribe/")
async def subscribe(pk: int, user: User = Depends(get_current_user)):
    if not user:
        return NOT_AUTHENTICATED
    if await db_follow.delete(user.id, pk):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
