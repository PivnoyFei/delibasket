from typing import Any, Optional

from fastapi import Form
from pydantic import BaseModel

from application.recipes.models import Recipe
from application.schemas import BaseSchema
from application.tags.schemas import TagOut
from application.users.schemas import UserOut


class IngredientOut(BaseSchema):
    name: str
    measurement_unit: str


class AmountOut(IngredientOut):
    amount: int

    @staticmethod
    async def tuple_to_dict(ingredients: tuple) -> dict[str, Any]:
        return [
            {"id": pk, "name": name, "measurement_unit": measurement_unit, "amount": amount}
            for pk, name, measurement_unit, amount in ingredients
        ]


class CreateAmountIngredient(BaseModel):
    id: int = 0
    amount: int | str = 0


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
            {"recipe_id": recipe_id, "ingredient_id": items.id, "amount": int(items.amount)}
            for items in self.ingredients
        ]


class CreateRecipe(BaseRecipe):
    text: str = Form(..., description="Описание")
    name: str = Form(..., max_length=200, description="Название")
    image: str = Form(..., description="Ссылка на картинку на сайте")
    cooking_time: int = Form(..., min_value=1, description="Время приготовления (в минутах)")
    ingredients: list[CreateAmountIngredient] = Form(..., description="Список ингредиентов")
    tags: list[int] = Form(..., description="Список тегов")

    class ConfigDict:
        str_strip_whitespace = True
        json_schema_extra = {
            "example": {
                "tags": [1, 2],
            }
        }

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
    ingredients: list[AmountOut] | None = None
    text: str
    cooking_time: int
    is_favorited: bool = False
    is_in_shopping_cart: bool = False

    @staticmethod
    async def to_dict(
        recipe: "RecipeOut",
        author: UserOut | None = None,
        is_favorited: Optional[int] = False,
        is_in_shopping_cart: Optional[int] = False,
    ) -> dict[str, Any]:
        """сложные запросы двойное соединение `Favorite` и `Cart` к `User` создает ошибку."""
        if not isinstance(is_favorited, bool):
            is_favorited = True if is_favorited else False
        if not isinstance(is_in_shopping_cart, bool):
            is_in_shopping_cart = True if is_in_shopping_cart else False

        return {
            "id": recipe.id,
            "name": recipe.name,
            "image": recipe.image,
            "tags": await TagOut.tuple_to_dict(recipe.tags),
            "author": author if author else recipe.author,
            "text": recipe.text,
            "cooking_time": recipe.cooking_time,
            "is_favorited": is_favorited,
            "is_in_shopping_cart": is_in_shopping_cart,
        }
