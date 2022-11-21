from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, root_validator


class UserRegistration(BaseModel):
    email: EmailStr = Field(...,)
    username: str = Field(..., min_length=5, max_length=150)
    first_name: str = Field(..., max_length=255)
    last_name: str = Field(..., max_length=255)


class UserCreate(UserRegistration):
    password: str = Field(..., min_length=5, max_length=255)


class UserAuth(BaseModel):
    email: EmailStr = Field(...,)
    password: str = Field(...,)


class TokenBase(BaseModel):
    auth_token: str


class UserSchemas(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_subscribed: bool = False


class UserBase(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    is_subscribed: bool = False


class Body(BaseModel):
    count: int
    next: str | None = None
    previous: str | None = None


class ListUsers(Body):
    results: list[UserSchemas] = []


class Follow(UserBase):
    recipes: Optional[list] = []
    recipes_count: Optional[int] = 0


class Subscriptions(Body):
    results: list[Follow] = []


class SetPassword(BaseModel):
    current_password: str = Field(..., description="old password")
    new_password: str = Field(..., description="New Password")

    @root_validator()
    def validator(cls, value):
        print(value)
        if value["current_password"] == value["new_password"]:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Incorrect password"
            )
        return value
