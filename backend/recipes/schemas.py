import json

from fastapi import Form
from pydantic import BaseModel

from users.schemas import Body, UserSchemas


class Tag(BaseModel):
    name: str = Form()
    color: str = Form(min_length=6, max_length=6)
    slug: str = Form()


class Tags(BaseModel):
    id: int
    name: str
    color: str
    slug: str


class Ingredient(BaseModel):
    name: str = Form()
    measurement_unit: str = Form()


class Ingredients(BaseModel):
    id: int
    name: str
    measurement_unit: str


class Amount(Ingredients):
    amount: int


class AmountIngredient(BaseModel):
    ingredient_id: int = 0
    amount: int = 0

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class Favorite(BaseModel):
    id: int
    name: str
    image: str
    cooking_time: int


class Recipe(BaseModel):
    id: int
    name: str
    image: str
    tags: list[Tags]
    author: UserSchemas
    ingredients: list[Amount]
    text: str
    cooking_time: int
    is_favorited: bool = False
    is_in_shopping_cart: bool = False


class listRecipe(Body):
    results: list[Recipe] | None = []
