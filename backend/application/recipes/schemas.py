import json
from typing import Any

from fastapi import Form, Query
from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from application.users.schemas import Body, UserOut


@dataclass
class QueryParams:
    tags: list[int | str] = Query(None)


class STag(BaseModel):
    name: str = Form()
    color: str = Form(min_length=6, max_length=6)
    slug: str = Form()


class TagOut(BaseModel):
    id: int
    name: str
    color: str
    slug: str

    class Config:
        orm_mode = True


class SIngredient(BaseModel):
    name: str = Form()
    measurement_unit: str = Form()


class IngredientOut(BaseModel):
    id: int
    name: str
    measurement_unit: str

    class Config:
        orm_mode = True


class AmountOut(IngredientOut):
    amount: int

    class Config:
        orm_mode = True


class SAmountIngredient(BaseModel):
    id: int = 0
    amount: int | str = 0

    @classmethod
    def __get_validators__(cls) -> Any:
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value: Any) -> Any:
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class FavoriteOut(BaseModel):
    id: int
    name: str
    image: str
    cooking_time: int


class CreateRecipe(BaseModel):
    text: str = Form(...)
    name: str = Form(...)
    image: str = Form(...)
    cooking_time: int = Form(...)
    ingredients: list[SAmountIngredient] = Form(...)
    tags: list[int] = Form(...)


class PatchRecipe(BaseModel):
    text: str = Form(...)
    name: str = Form(...)
    image: str | None
    cooking_time: int = Form(...)
    ingredients: list[SAmountIngredient] = Form(...)
    tags: list[int] = Form(...)


class RecipeField(BaseModel):
    id: int
    name: str
    image: str
    author: int
    text: str
    cooking_time: int
    is_favorited: bool
    is_in_shopping_cart: bool

    class Config:
        orm_mode = True


class RecipeOut(BaseModel):
    id: int
    name: str
    image: str
    tags: list[TagOut]
    author: UserOut
    ingredients: list[AmountOut]
    text: str
    cooking_time: int
    is_favorited: bool = False
    is_in_shopping_cart: bool = False

    class Config:
        orm_mode = True


class listRecipe(Body):
    results: list[RecipeOut] | None = []
