from typing import Optional
#from fastapi.param_functions import Form
from fastapi import Form
from pydantic import BaseModel, EmailStr


class UserRegistration(BaseModel):
    email: EmailStr
    username: str = Form(min_length=5, max_length=150)
    first_name: str = Form(max_length=255)
    last_name: str = Form(max_length=255)


class UserCreate(UserRegistration):
    password: str = Form(min_length=5, max_length=255)


class UserAuth(BaseModel):
    email: str = Form()
    password: str = Form()


class UserToken(BaseModel):
    auth_token: str


class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_subscribed: Optional[str | bool] = False


class ListUsers(BaseModel):
    count: int
    results: list[User] = []


class Follow(User):
    recipes: Optional[list] = []
    recipes_count: Optional[int] = 0


class Subscriptions(BaseModel):
    count: int
    results: list[Follow] = []


class SetPassword(BaseModel):
    password: str
    last_name: str
    email: str


class TokenPayload(BaseModel):
    sub: int = None
    exp: int = None