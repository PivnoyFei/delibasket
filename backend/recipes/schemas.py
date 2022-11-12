import json

from fastapi import Form
from pydantic import BaseModel


class Tag(BaseModel):
    name: str = Form()
    color: str = Form(min_length=6, max_length=6)
    slug: str = Form()


class Ingredient(BaseModel):
    name: str = Form()
    measurement_unit: str = Form()


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


class Recipe(BaseModel):
    name: str
    text: str
    cooking_time: int
    ingredients: list[AmountIngredient] = Form(...)
    tags: list[int] = Form(...)
