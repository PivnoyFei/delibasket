import logging

from sqlalchemy import Result, delete, func, insert, select

from application.database import scoped_session
from application.ingredients.models import AmountIngredient, Ingredient
from application.ingredients.schemas import IngredientRecipeCreate

logger = logging.getLogger(__name__)


class IngredientManager:
    async def get_amount_ingredient(self, recipe_id: int) -> Result | None:
        async with scoped_session() as session:
            try:
                query = await session.execute(
                    select(
                        Ingredient.id,
                        Ingredient.name,
                        Ingredient.measurement_unit,
                        AmountIngredient.amount,
                    )
                    .join(AmountIngredient.ingredient)
                    .where(AmountIngredient.recipe_id == recipe_id)
                )
                return query.all()
            except Exception as e:
                await session.rollback()
                logger.error(e)
                return None

    async def create_amount_ingredient(self, ingredient_in: IngredientRecipeCreate) -> bool:
        async with scoped_session() as session:
            try:
                await session.execute(
                    insert(AmountIngredient).values(await ingredient_in.to_list())
                )
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                logger.error(e)
                return False

    async def delete_amount_ingredient(self, recipe_id: int) -> Result | None:
        async with scoped_session() as session:
            try:
                return await session.execute(
                    delete(AmountIngredient).where(AmountIngredient.recipe_id == recipe_id)
                )
            except Exception as e:
                await session.rollback()
                logger.error(e)
                return None

    async def update_amount_ingredient(self, ingredient_in: IngredientRecipeCreate) -> bool:
        async with scoped_session() as session:
            try:
                await session.execute(
                    delete(AmountIngredient).where(AmountIngredient.recipe_id == ingredient_in.id)
                )
                await session.execute(
                    insert(AmountIngredient).values(await ingredient_in.to_list())
                )
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                logger.error(e)
                return False

    async def get_shopping_cart(self, recipe_id: list[int]) -> list:
        async with scoped_session() as session:
            query = await session.execute(
                select(
                    Ingredient.id,
                    Ingredient.name,
                    Ingredient.measurement_unit,
                    func.sum(AmountIngredient.amount).label("amount"),
                )
                .filter(AmountIngredient.recipe_id.in_(recipe_id))
                .join(AmountIngredient.ingredient)
                .group_by(Ingredient.id, Ingredient.name, Ingredient.measurement_unit)
            )
            return query.all()
