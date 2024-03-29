# flake8: noqa: F401
""" Генерирует рандомные рецепты для тестов. """

import asyncio
import random
import string
import uuid

import __init__
from sqlalchemy import insert

from application.database import sessionmanager
from application.recipes.models import Recipe
from application.services import delete_is_ingredients, post_is_ingredients
from application.settings import settings
from application.tags.models import recipe_tag


async def async_main() -> None:
    sessionmanager.init(settings.SQLALCHEMY_DATABASE_URI, "recipe")
    async with sessionmanager.scoped_session("recipe") as session:
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
                    "ingredient_id": random.randint(1, 2186),
                    "amount": random.randint(1, 100),
                }
                if ingredient["id"] not in was:
                    was.append(ingredient["id"])
                    ingredients.append(ingredient)

            if post_is_ingredients({"id": recipe_id, "ingredients": ingredients}):
                await session.commit()
            else:
                await session.rollback()
                delete_is_ingredients(recipe_id)
                break

    await sessionmanager.close("recipe")


asyncio.run(async_main())
