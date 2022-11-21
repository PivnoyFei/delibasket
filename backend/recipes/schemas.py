import json

from fastapi import Form
from pydantic import BaseModel

from users.schemas import Body, UserSchemas


class STag(BaseModel):
    name: str = Form()
    color: str = Form(min_length=6, max_length=6)
    slug: str = Form()


class STags(BaseModel):
    id: int
    name: str
    color: str
    slug: str


class SIngredient(BaseModel):
    name: str = Form()
    measurement_unit: str = Form()


class SIngredients(BaseModel):
    id: int
    name: str
    measurement_unit: str


class SAmount(SIngredients):
    amount: int


class SAmountIngredient(BaseModel):
    id: int = 0
    amount: int | str = 0

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class SFavorite(BaseModel):
    id: int
    name: str
    image: str
    cooking_time: int


class SLoadRecipe(BaseModel):
    text: str = Form(...)
    name: str = Form(...)
    image: str = Form(...)
    cooking_time: int = Form(...)
    ingredients: list[SAmountIngredient] = Form(...)
    tags: list[int] = Form(...)


class SRecipe(BaseModel):
    id: int
    name: str
    image: str
    tags: list[STags]
    author: UserSchemas
    ingredients: list[SAmount]
    text: str
    cooking_time: int
    is_favorited: bool = False
    is_in_shopping_cart: bool = False


class SlistRecipe(Body):
    results: list[SRecipe] | None = []
