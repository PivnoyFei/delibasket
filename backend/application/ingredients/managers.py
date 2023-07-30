from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.ingredients.models import AmountIngredient, Ingredient
from application.recipes.schemas import AmountOut


class AmountManager:
    @staticmethod
    async def get_amount(session: AsyncSession, pk: int) -> list[AmountOut]:
        amount_dict = await session.execute(
            select(
                Ingredient.id,
                Ingredient.name,
                Ingredient.measurement_unit,
                AmountIngredient.amount,
            )
            .join(Ingredient, AmountIngredient.ingredient_id == Ingredient.id)
            .where(AmountIngredient.recipe_id == pk)
        )
        return amount_dict.all()


class IngredientManager:
    pass
