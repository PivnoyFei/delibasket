from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, constr, root_validator, validator

from application.schemas import BaseSchema, name_str
from application.utils import hash_password


class UserRegistration(BaseModel):
    email: EmailStr
    username: str = Field(min_length=5, max_length=128)
    first_name: str = Field(max_length=255)
    last_name: str = Field(max_length=255)


class UserCreate(BaseModel):
    username: str = Field(min_length=5, max_length=150)
    first_name: constr(regex=name_str, max_length=150) = Field(min_length=1)
    last_name: constr(regex=name_str, max_length=150) = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=7, max_length=256)

    class Config:
        anystr_strip_whitespace = True

    @validator("password", pre=True)
    def hash(cls, v: Any) -> bytes:
        return hash_password(v)


class UserOut(BaseSchema):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_subscribed: bool | None = False


class UserBase(BaseSchema):
    username: str
    first_name: str
    last_name: str
    is_subscribed: bool = False


class FavoriteOut(BaseSchema):
    id: int
    name: str
    image: str
    cooking_time: int


class FollowOut(UserBase):
    recipes: list[FavoriteOut] | None = []
    recipes_count: int = 0

    @staticmethod
    async def to_dict(user: UserOut, recipes: FavoriteOut) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_subscribed": True,
            "recipes": recipes,
            "recipes_count": len(recipes),
        }


class SetPassword(BaseModel):
    current_password: str = Field(description="old password")
    new_password: str = Field(description="New Password")

    @root_validator()
    def validator(cls, value: dict) -> dict:
        if value["current_password"] == value["new_password"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password")
        value["new_password"] = hash_password(value["new_password"])
        return value
