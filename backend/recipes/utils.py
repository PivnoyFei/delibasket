import base64
import binascii
import os
from typing import Any
from uuid import uuid4

import aiofiles
from fastapi import status
from fastapi.responses import JSONResponse
from recipes.models import FavoriteCartDB, RecipeDB
from recipes.schemas import FavoriteOut
from settings import (ALLOWED_TYPES, INVALID_FILE, INVALID_TYPE, MEDIA_ROOT,
                      NOT_AUTHENTICATED, NOT_FOUND)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException
from starlette.requests import Request
from users.models import User


async def tag_ingredient(
    session: AsyncSession, db_model: Any, item: Any, user: User, pk: int | None = None
) -> JSONResponse:
    """ Распределяет модели создания и редактирования тегов и ингредиентов. """
    if not user:
        return NOT_AUTHENTICATED
    if user.is_staff or user.is_superuser:
        e = await db_model(session, item, pk)
        if e and type(e) not in (int, dict):
            e = str(e).split(": ")[-1]
            return JSONResponse(f"Incorrect {e}", status.HTTP_400_BAD_REQUEST)
        return JSONResponse(e, status_code=status.HTTP_200_OK)
    return JSONResponse("No access", status_code=status.HTTP_403_FORBIDDEN)


async def create_cart_favorite(
    request: Request, pk: int, user: User, db_model: Any, session: AsyncSession
) -> JSONResponse | list[FavoriteOut]:
    """ Распределяет модели подписки на рецепт и добавления в корзину. """
    if not user:
        return NOT_AUTHENTICATED
    recipe = await RecipeDB.check_recipe_by_id_author(session, request, recipe_id=pk)
    if recipe:
        if not await FavoriteCartDB.create(session, pk, user.id, db_model):
            return JSONResponse({"detail": "Already added"}, status.HTTP_400_BAD_REQUEST)
    return recipe or NOT_FOUND


async def delete_cart_favorite(pk: int, user: User, db_model: Any, session: AsyncSession) -> JSONResponse:
    """ Распределяет модели отписки от рецепта и удаление из корзины. """
    if not user:
        return NOT_AUTHENTICATED
    if not await FavoriteCartDB.delete(session, pk, user.id, db_model):
        return JSONResponse({"detail": "Already deleted"}, status.HTTP_400_BAD_REQUEST)
    return JSONResponse({"detail": "Deleted"}, status.HTTP_204_NO_CONTENT)


async def base64_image(base64_data: str, extension: str = "jpg") -> tuple[str, str]:
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
