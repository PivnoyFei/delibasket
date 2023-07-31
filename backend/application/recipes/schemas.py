import json
from typing import Any, Optional

from fastapi import Form, Query
from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from application.recipes.models import Recipe
from application.schemas import BaseSchema
from application.users.schemas import UserOut


@dataclass
class QueryParams:
    tags: list[int | str] = Query(None)


class TagOut(BaseSchema):
    name: str
    color: str
    slug: str


class IngredientOut(BaseSchema):
    name: str
    measurement_unit: str


class AmountOut(IngredientOut):
    amount: int


class CreateAmountIngredient(BaseModel):
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


class FavoriteOut(BaseSchema):
    name: str
    image: str
    cooking_time: int


class BaseRecipe(BaseModel):
    async def to_dict(self) -> NotImplementedError:
        raise NotImplementedError("Метод должен быть переопределен.")

    async def tags_to_list(self, recipe_id: int) -> list[dict[str, int]]:
        return [{"recipe_id": recipe_id, "tag_id": pk} for pk in self.tags]

    async def ingredients_to_list(self, recipe_id: int) -> list[dict[str, int]]:
        return [
            {"recipe_id": recipe_id, "ingredient_id": items["id"], "amount": int(items["amount"])}
            for items in self.ingredients
        ]


class CreateRecipe(BaseRecipe):
    text: str = Form(...)
    name: str = Form(...)
    image: str = Form(...)
    cooking_time: int = Form(...)
    ingredients: list[CreateAmountIngredient] = Form(...)
    tags: list[int] = Form(...)

    async def to_dict(self, author_id: int, filename: str) -> dict[str, Any]:
        return {
            "author_id": author_id,
            "text": self.text,
            "name": self.name,
            "image": filename,
            "cooking_time": self.cooking_time,
        }


class UpdateRecipe(BaseRecipe):
    text: str | None = None
    name: str | None = None
    image: str | None = None
    cooking_time: int | None = None
    ingredients: list[CreateAmountIngredient] | None = None
    tags: list[int] | None = None

    async def to_dict(self, recipe: Recipe, filename: str | None = None) -> dict[str, Any]:
        result = {"image": filename} if filename else {}
        for item in ("text", "name", "cooking_time", "text"):
            if change := getattr(self, item, None):
                if change != getattr(recipe, item, None):
                    result[item] = change
        return result


class RecipeOut(BaseSchema):
    name: str
    image: str
    tags: list[TagOut]
    author: UserOut
    ingredients: list[AmountOut]
    text: str
    cooking_time: int
    is_favorited: bool = False
    is_in_shopping_cart: bool = False

    @staticmethod
    async def to_dict(
        recipe: Recipe,
        ingredients: list,
        author: UserOut | None = None,
        is_favorited: Optional[int] = False,
        is_in_shopping_cart: Optional[int] = False,
    ) -> dict[str, Any]:
        """сложные запросы двойное соединение `Favorite` и `Cart` к `User` создает ошибку.
        author:
        ingredients: пока так."""
        if not isinstance(is_favorited, bool):
            is_favorited = True if is_favorited else False
        if not isinstance(is_in_shopping_cart, bool):
            is_in_shopping_cart = True if is_in_shopping_cart else False
        return {
            "id": recipe.id,
            "name": recipe.name,
            "image": recipe.image,
            "tags": recipe.tags,
            "author": author if author else recipe.author,
            "ingredients": ingredients,
            "text": recipe.text,
            "cooking_time": recipe.cooking_time,
            "is_favorited": is_favorited,
            "is_in_shopping_cart": is_in_shopping_cart,
        }
