import os

import httpx

from application.settings import MEDIA_ROOT, settings


async def image_delete(filename: str = "", image_path: str = "") -> None:
    if not image_path:
        image_path = os.path.join(MEDIA_ROOT, filename)
    if os.path.isfile(image_path):
        os.remove(image_path)


async def get_is_ingredients(recipe_id: int):
    response = httpx.get(settings.INGREDIENTS_URL + f"{recipe_id}/")
    return response.json() if response.status_code == 200 else False


async def get_shopping_cart(in_data: list[int]):
    response = httpx.get(settings.INGREDIENTS_URL + "shopping_cart/", json=in_data)
    return response.json() if response.status_code == 200 else False


async def delete_is_ingredients(recipe_id: int):
    response = httpx.delete(settings.INGREDIENTS_URL + f"{recipe_id}/")
    return True if response.status_code == 200 else False


async def post_is_ingredients(in_data: dict):
    response = httpx.post(settings.INGREDIENTS_URL, json=in_data)
    return True if response.status_code == 200 else False


async def update_is_ingredients(in_data: dict):
    response = httpx.put(settings.INGREDIENTS_URL, json=in_data)
    return True if response.status_code == 200 else False
