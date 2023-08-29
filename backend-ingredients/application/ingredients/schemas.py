from typing import Any

from fastapi import Form
from pydantic import BaseModel

from application.schemas import BaseSchema


class IngredientCreate(BaseModel):
    name: str = Form(..., description="Название")
    measurement_unit: str = Form(..., description="Единицы измерения")

    class ConfigDict:
        str_strip_whitespace = True
        json_schema_extra = {
            "example": {
                "name": "Капуста",
                "measurement_unit": "кг",
            }
        }


class IngredientUpdate(BaseModel):
    name: str | None = None
    measurement_unit: str | None = None


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
    ingredient_id: int = 0
    amount: int | str = 0


class IngredientRecipeCreate(BaseSchema):
    ingredients: list[CreateAmountIngredient] = Form(..., description="Список ингредиентов")

    async def to_list(self) -> list[dict[str, int]]:
        return [
            {
                "recipe_id": self.id,
                "ingredient_id": items.ingredient_id,
                "amount": int(items.amount),
            }
            for items in self.ingredients
        ]
