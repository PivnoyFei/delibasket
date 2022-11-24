import random
import string

import sqlalchemy

from recipes.models import amount_ingredient, recipe, recipe_tag
from settings import DATABASE_URL

engine = sqlalchemy.create_engine(DATABASE_URL)
engine.connect()
metadata = sqlalchemy.MetaData(engine)
metadata.reflect(engine)

""" Генерирует рандомные рецепты для тестов. """
for recipe_id in range(1, 101):
    letters = string.ascii_lowercase
    name = ''.join(random.choice(letters) for i in range(20))
    recipe_item = {
        "author_id": "1",
        "name": name,
        "image": f"image{recipe_id}.png",
        "text": name,
        "cooking_time": random.randint(1, 255)
    }
    engine.execute(recipe.insert().values(recipe_item))

    tags = [
        {"recipe_id": recipe_id, "tag_id": tag_id}
        for tag_id in range(1, random.randint(2, 4))
    ]
    engine.execute(recipe_tag.insert().values(tags))

    ingredients = []
    was = []
    for _ in range(random.randint(1, 5)):
        ingredient = {
            "recipe_id": recipe_id,
            "ingredient_id": random.randint(1, 2186),
            "amount": random.randint(1, 100)
        }
        if ingredient["ingredient_id"] not in was:
            was.append(ingredient["ingredient_id"])
            ingredients.append(ingredient)

    engine.execute(amount_ingredient.insert().values(ingredients))
