from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse

from db import database
from users import utils
from users.models import User
from users.schemas import GetUser, UserInDB, UserCreate, UserAuth, Userfull

user_router = APIRouter(prefix='/api', tags=["users"])
db_user = User(database)


@user_router.post("/users/", response_model=GetUser)
async def create_user(data: UserCreate):
    if await db_user.get_user_by_email(data.email):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Email already exists"}
        )
    if await db_user.get_user_by_username(data.username):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Username already exists"}
        )
    data.password = await utils.get_hashed_password(data.password)
    await db_user.create_user(data)
    return await db_user.get_user_full_by_email(data.email)


@user_router.post("/auth/token/login/", response_model=UserInDB)
async def login(data: UserAuth = Depends()):
    user_dict = await db_user.get_user_password_by_email(data.email)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect email")
    if not await utils.verify_password(data.password, user_dict["password"]):
        raise HTTPException(status_code=400, detail="Incorrect password")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"auth_token": await utils.create_access_token(data.email)}
    )


@user_router.get("/users/me/")
async def read_users_me(current_user: User = Depends(utils.get_current_user)):
    return current_user


@user_router.get("/users/{pk}/", response_model=Userfull)
async def read_users_pk(pk: int, current_user: User = Depends(utils.get_current_user)):
    user_dict = await db_user.get_user_full_by_id(pk)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect user")
    return user_dict
