from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordRequestForm

from db import database
from recipes.models import Recipe
from services import query_list
from settings import NOT_AUTHENTICATED, NOT_FOUND
from users import schemas, utils
from users.models import Follow, User

user_router = APIRouter(prefix='/api', tags=["users"])
db_recipe = Recipe(database)
db_user = User(database)
db_follow = Follow(database)


@user_router.get("/users/", response_model=schemas.ListUsers)
async def users(user: User = Depends(utils.get_current_user)):
    """Список пользователей."""
    user = await db_user.get_users(user.id if user else None)
    return await query_list(user)


@user_router.post("/users/", response_model=schemas.UserRegistration)
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
    user.password = await utils.get_hashed_password(user.password)
    user_id = await db_user.create_user(user)
    return await db_user.get_user_full_by_id(user_id)


@user_router.post("/auth/token/login/", response_model=schemas.UserToken)
async def login(user: schemas.UserAuth):
    """Авторизация по емейлу и паролю, выдает токен."""
    user = OAuth2PasswordRequestForm(
        username=user.email, password=user.password, scope="me"
    )
    user_dict = await db_user.get_user_password_id_by_email(user.username)
    if not user_dict:
        return JSONResponse("Incorrect email", status.HTTP_400_BAD_REQUEST)
    if not await utils.verify_password(user.password, user_dict["password"]):
        return JSONResponse("Incorrect password", status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        {"auth_token": await utils.create_access_token(user_dict["id"])},
        status.HTTP_200_OK
    )


@user_router.get("/users/me/", response_model=schemas.UserSchemas)
async def me(user: User = Depends(utils.get_current_user)):
    """Текущий пользователь."""
    return user or NOT_AUTHENTICATED


@user_router.get("/users/subscriptions/", response_model=schemas.Subscriptions)
async def subscriptions(user: User = Depends(utils.get_current_user)):
    """
    Мои подписки.
    Возвращает пользователей, на которых подписан текущий пользователь.
    В выдачу добавляются рецепты.
    """
    results = await db_follow.is_subscribed_all(user.id)
    if results:
        results = [dict(i) for i in results]
        for user_dict in results:
            recipes = await db_recipe.get_recipe_by_author(user_dict["id"])
            user_dict["recipes"] = recipes
            user_dict["recipes_count"] = len(recipes)
        return await query_list(results)
    return Response(status_code=status.HTTP_401_UNAUTHORIZED)


@user_router.get("/users/{pk}/", response_model=schemas.UserSchemas)
async def user_id(pk: int, user: User = Depends(utils.get_current_user)):
    """Профиль пользователя. Доступно всем пользователям."""
    if user:
        user = await db_user.get_user_full_by_id_auth(pk, user.id)
    else:
        user = await db_user.get_user_full_by_id(pk)
    return user or NOT_FOUND


@user_router.post("/users/{pk}/subscribe/", response_model=schemas.Follow)
async def create_subscribe(
    pk: int, user: User = Depends(utils.get_current_user)
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
    recipes = await db_recipe.get_recipe_by_author(pk)
    autor_dict["recipes"] = recipes
    autor_dict["recipes_count"] = len(recipes)
    return autor_dict


@user_router.delete("/users/{pk}/subscribe/")
async def subscribe(pk: int, user: User = Depends(utils.get_current_user)):
    if not user:
        return NOT_AUTHENTICATED
    if await db_follow.delete(user.id, pk):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
