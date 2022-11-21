import base64
import binascii
import os
from uuid import uuid4

import aiofiles
from fastapi import Query, status
from fastapi.responses import JSONResponse, Response
from pydantic.dataclasses import dataclass

from db import database
from recipes.models import FavoriteCart, Recipe
from settings import ALLOWED_TYPES, MEDIA_ROOT, NOT_AUTHENTICATED, NOT_FOUND

db_favorite_cart = FavoriteCart(database)
db_recipe = Recipe(database)


@dataclass
class QueryParams:
    tags: list[int | str] = Query(None)


async def create_tag_ingredient(db_model, item, user):
    if not user:
        return NOT_AUTHENTICATED
    if user.is_superuser or user.is_staff is True:
        e = await db_model(item)
        if type(e) != int:
            e = str(e).split(": ")[-1]
            return JSONResponse(f"Incorrect {e}", status.HTTP_400_BAD_REQUEST)
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_403_FORBIDDEN)


async def create_cart_favorite(request, pk, user, db_model):
    if not user:
        return NOT_AUTHENTICATED
    recipe = await db_recipe.check_recipe_by_id_author(request, recipe_id=pk)
    if recipe:
        if not await db_favorite_cart.create(pk, user.id, db_model):
            return JSONResponse(
                {"detail": "Already added"}, status.HTTP_400_BAD_REQUEST)
    print("recipe", recipe)
    return recipe or NOT_FOUND


async def delete_cart_favorite(pk, user, db_model) -> JSONResponse | Response:
    if not user:
        return NOT_AUTHENTICATED
    await db_favorite_cart.delete(pk, user.id, db_model)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def base64_image(base64_data, extension="jpg") -> tuple[str, str]:
    if ";base64," in base64_data:
        header, base64_data = base64_data.split(";base64,")
        name, extension = header.split("/")

        if extension.lower() not in ALLOWED_TYPES:
            raise JSONResponse(
                {"detail": "Invalid image format"},
                status.HTTP_400_BAD_REQUEST
            )

    filename = f"{uuid4()}.{extension}"
    image_path = os.path.join(MEDIA_ROOT, filename)

    # base64_data = base64.decodebytes(bytes(recipe.image, "utf-8"))
    # image = Image.open(BytesIO(base64_data))
    # image.save(image_path)
    try:
        async with aiofiles.open(image_path, "wb") as buffer:
            await buffer.write(base64.b64decode(base64_data))
    except (Exception, TypeError, binascii.Error, ValueError):
        raise JSONResponse(
            {"detail": "Error encoding file"},
            status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    return filename, image_path
