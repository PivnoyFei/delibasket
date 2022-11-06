from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, Response
from typing import Optional
from db import database
from users import utils, schemas
from users.models import User, Follow
from users.services import users_list

user_router = APIRouter(prefix='/api', tags=["users"])
db_user = User(database)
db_follow = Follow(database)


@user_router.get("/users/")#, response_model=schemas.ListUserfull)
async def users(user_dict: User = Depends(utils.get_current_user)):
    """Список пользователей."""
    user_dict = await db_user.get_users_all(user_dict["id"])
    print("====", user_dict)
    return await users_list(user_dict)


@user_router.post("/users/", response_model=schemas.GetUser)
async def create_user(user: schemas.UserCreate):
    if await db_user.get_user_by_email(user.email):
        return JSONResponse(
            {"message": "Email already exists"},
            status.HTTP_400_BAD_REQUEST
        )
    if await db_user.get_user_by_username(user.username):
        return JSONResponse(
            {"message": "Username already exists"},
            status.HTTP_400_BAD_REQUEST
        )
    user.password = await utils.get_hashed_password(user.password)
    user_id = await db_user.create_user(user)
    return await db_user.get_user_full_by_id(user_id)


@user_router.post("/auth/token/login/", response_model=schemas.UserToken)
async def login(user: schemas.UserAuth = Depends()):
    """Используется для авторизации по емейлу и паролю, чтобы далее использовать токен при запросах."""
    user_dict = await db_user.get_user_password_id_by_email(user.email)
    if not user_dict:
        return JSONResponse("Incorrect email", status.HTTP_400_BAD_REQUEST)
    if not await utils.verify_password(user.password, user_dict["password"]):
        return JSONResponse("Incorrect password", status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        {"auth_token": await utils.create_access_token(user_dict["id"])},
        status.HTTP_200_OK
    )


@user_router.get("/users/me/", response_model=schemas.Userfull)
async def me(user_dict: User = Depends(utils.get_current_user)):
    """Текущий пользователь."""
    return user_dict


@user_router.get("/users/subscriptions/", response_model=schemas.Subscriptions)
async def subscriptions(user_dict: User = Depends(utils.get_current_user)):
    """
    Мои подписки.
    Возвращает пользователей, на которых подписан текущий пользователь.
    В выдачу добавляются рецепты.
    """
    results = await db_follow.is_subscribed_all(user_dict["id"])
    return await users_list(results)


@user_router.get("/users/{pk}/", response_model=schemas.Userfull)
async def user_pk(pk: int, user: User = Depends(utils.get_current_user)):
    """
    Профиль пользователя.
    Доступно всем пользователям.
    """
    user_dict = await db_user.get_user_full_by_id(pk)
    if not user_dict:
        return JSONResponse("Incorrect user", status.HTTP_400_BAD_REQUEST)
    return user_dict


@user_router.post("/users/{pk}/subscribe/", response_model=schemas.Userfull)
async def subscribe(pk: int, user_dict: User = Depends(utils.get_current_user)):
    autor_dict = await db_user.get_user_full_by_id(pk)
    if not autor_dict:
        return JSONResponse("Incorrect user", status.HTTP_400_BAD_REQUEST)
    if pk == user_dict["id"]:
        return JSONResponse(
            {'errors': 'It is forbidden to unfollow or follow yourself.'},
            status.HTTP_400_BAD_REQUEST
        )
    if await db_follow.is_subscribed(user_dict["id"], pk):
        return JSONResponse(
            {'errors': 'You are already subscribed to this author.'},
            status.HTTP_400_BAD_REQUEST
        )
    await db_follow.create(user_dict["id"], pk)
    # "recipes": [],
    # "recipes_count": 0  # добавить
    print("====", autor_dict)
    autor_dict["is_subscribed"] = True
    print("====", autor_dict)
    return autor_dict


@user_router.delete("/users/{pk}/subscribe/")
async def subscribe(pk: int, user_dict: User = Depends(utils.get_current_user)):
    if await db_follow.delete(user_dict["id"], pk):
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


#{
#    "count": 2,
#    "next": null,
#    "previous": null,
#    "results": [
#        {
#            "id": 2,
#            "username": "string",
#            "first_name": "string",
#            "last_name": "string",
#            "is_subscribed": true,
#            "recipes": [],
#            "recipes_count": 0
#        },
#        {
#            "id": 3,
#            "username": "strings",
#            "first_name": "strings",
#            "last_name": "strings",
#            "is_subscribed": true,
#            "recipes": [],
#            "recipes_count": 0
#        }
#    ]
#}