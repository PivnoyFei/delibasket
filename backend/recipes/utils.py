import base64
import binascii
import os
from uuid import uuid4

import aiofiles
from fastapi import Query, status
from fastapi.responses import JSONResponse, Response
from pydantic.dataclasses import dataclass
from starlette.exceptions import HTTPException

from db import database
from recipes.models import FavoriteCart, Ingredient, Recipe, Tag
from settings import (ALLOWED_TYPES, INVALID_FILE, INVALID_TYPE, MEDIA_ROOT,
                      NOT_AUTHENTICATED, NOT_FOUND)

db_tag = Tag(database)
db_recipe = Recipe(database)
db_ingredient = Ingredient(database)
db_favorite_cart = FavoriteCart(database)


@dataclass
class QueryParams:
    tags: list[int | str] = Query(None)


async def check_tags(tags):
    """ Проверка наличия в бд, всех тегов из списка. """
    for i in tags:
        if not await db_tag.get_tags(i):
            raise JSONResponse(
                {"detail": f"Not tag {i}"}, status.HTTP_404_NOT_FOUND
            )
    return True


async def check_ingredient(ingredients):
    """ Проверка наличия в бд, всех ингредиентов из списка. """
    for i in ingredients:
        i = i["id"]
        if not await db_ingredient.get_ingredient(i):
            raise JSONResponse(
                {"detail": f"Not ingredient {i}"}, status.HTTP_404_NOT_FOUND
            )
    return True


async def utils_tag_ingredient(db_model, item, user, pk=None):
    """ Распределяет модели создания и редактирования тегов и ингредиентов. """
    if not user:
        return NOT_AUTHENTICATED
    if user.is_staff or user.is_superuser:
        e = await db_model(item, pk)
        if type(e) != int:
            e = str(e).split(": ")[-1]
            return JSONResponse(f"Incorrect {e}", status.HTTP_400_BAD_REQUEST)
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_403_FORBIDDEN)


async def create_cart_favorite(request, pk, user, db_model):
    """ Распределяет модели подписки на рецепт и добавления в корзину. """
    if not user:
        return NOT_AUTHENTICATED
    recipe = await db_recipe.check_recipe_by_id_author(request, recipe_id=pk)
    if recipe:
        if not await db_favorite_cart.create(pk, user.id, db_model):
            return JSONResponse(
                {"detail": "Already added"}, status.HTTP_400_BAD_REQUEST)
    return recipe or NOT_FOUND


async def delete_cart_favorite(pk, user, db_model) -> JSONResponse | Response:
    """ Распределяет модели отписки от рецепта и удаление из корзины. """
    if not user:
        return NOT_AUTHENTICATED
    await db_favorite_cart.delete(pk, user.id, db_model)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def base64_image(base64_data, extension="jpg") -> tuple[str, str]:
    """
    Проверяет формат файла если он есть.
    При удачном декодировании base64, файл будет сохранен.
    """
    if ";base64," in base64_data:
        header, base64_data = base64_data.split(";base64,")
        name, extension = header.split("/")
        if extension.lower() not in ALLOWED_TYPES:
            raise HTTPException(status.HTTP_418_IM_A_TEAPOT, INVALID_TYPE)

    filename = f"{uuid4()}.{extension}"
    image_path = os.path.join(MEDIA_ROOT, filename)

    try:
        async with aiofiles.open(image_path, "wb") as buffer:
            await buffer.write(base64.b64decode(base64_data))

    except (Exception, TypeError, binascii.Error, ValueError):
        raise HTTPException(status.HTTP_418_IM_A_TEAPOT, INVALID_FILE)

    return filename, image_path
