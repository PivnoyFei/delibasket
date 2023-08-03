from pydantic import BaseModel, EmailStr, Field, constr, field_validator, model_validator

from application.exceptions import BadRequestException
from application.schemas import BaseSchema, name_en_str, name_str
from application.utils import hash_password


class UserRegistration(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str


class UserCreate(BaseModel):
    username: constr(pattern=name_en_str, min_length=1, max_length=150)
    first_name: constr(pattern=name_str, min_length=1, max_length=150)
    last_name: constr(pattern=name_str, min_length=1, max_length=150)
    email: EmailStr
    password: str | bytes = Field(min_length=7)

    class Config:
        str_strip_whitespace = True
        json_schema_extra = {
            "example": {
                "email": "vpupkin@delibasket.ru",
                "username": "vasyapupkin",
                "first_name": "Вася",
                "last_name": "Пупкин",
                "password": "Qwerty123",
            }
        }

    @field_validator("password")
    @classmethod
    def hash(cls, v: str) -> bytes:
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

    @model_validator(mode='after')
    def validator(self) -> "SetPassword":
        if self.current_password == self.new_password:
            raise BadRequestException("Incorrect password")
        self.new_password = hash_password(self.new_password)
        return self
