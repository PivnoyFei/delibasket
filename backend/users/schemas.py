from typing import Optional

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


class UserSchemas(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_subscribed: Optional[str | bool] = False


class UserBase(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    is_subscribed: bool = False


class Body(BaseModel):
    count: int
    next: bool = None
    previous: bool = None


class ListUsers(Body):
    results: list[UserSchemas] = []


class Follow(UserBase):
    recipes: Optional[list] = []
    recipes_count: Optional[int] = 0


class Subscriptions(Body):
    results: list[Follow] = []


class SetPassword(BaseModel):
    password: str
    last_name: str
    email: str


class TokenPayload(BaseModel):
    sub: int = None
    exp: int = None
