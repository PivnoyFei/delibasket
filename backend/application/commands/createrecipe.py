# flake8: noqa: F401
""" Генерирует рандомные рецепты для тестов. """

import asyncio
import random
import string
import uuid

import __init__
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from application.ingredients.models import AmountIngredient
from application.recipes.models import Recipe
from application.settings import settings
from application.tags.models import recipe_tag


async def async_main() -> None:
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        for _ in range(1, 101):
            name = "".join(random.choice(string.ascii_lowercase) for i in range(20))
            recipe = {
                "author_id": 1,
                "name": name,
                "image": f"{uuid.uuid4().hex}.png",
                "text": name,
                "cooking_time": random.randint(1, 255),
            }
            query = await session.execute(insert(Recipe).values(recipe).returning(Recipe.id))
            recipe_id = query.fetchone()[0]

            tags = [
                {"recipe_id": recipe_id, "tag_id": tag_id}
                for tag_id in range(1, random.randint(2, 4))
            ]
            await session.execute(insert(recipe_tag).values(tags))

            ingredients = []
            was = []
            for _ in range(random.randint(1, 5)):
                ingredient = {
                    "recipe_id": recipe_id,
                    "ingredient_id": random.randint(1, 2186),
                    "amount": random.randint(1, 100),
                }
                if ingredient["ingredient_id"] not in was:
                    was.append(ingredient["ingredient_id"])
                    ingredients.append(ingredient)
            await session.execute(insert(AmountIngredient).values(ingredients))

        await session.commit()
    await engine.dispose()


asyncio.run(async_main())
