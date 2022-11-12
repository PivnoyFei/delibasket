import os

import aiofiles
from fastapi import APIRouter, Body, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse, Response

from db import database
from recipes import schemas
from recipes.models import Ingredient, Recipe, Tag
from services import query_list
from settings import STATIC_ROOT
from users.models import User
from users.utils import get_current_user

recipe_router = APIRouter(prefix='/api', tags=["recipe"])
db_user = User(database)
db_tag = Tag(database)
db_ingredient = Ingredient(database)
db_recipe = Recipe(database)


@recipe_router.post("/tags/")
async def create_tag(
    tag: schemas.Tag,
    user_dict: User = Depends(get_current_user)
):
    if user_dict["is_superuser"] or user_dict["is_staff"] == True:
        e = await db_tag.create_tag(tag)
        if type(e) != int:
            e = str(e).split(": ")[-1]
            return JSONResponse(f"Incorrect {e}", status.HTTP_400_BAD_REQUEST)
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_403_FORBIDDEN)


@recipe_router.get("/tags/")
async def tags():
    return await db_tag.get_tags()


@recipe_router.get("/tags/{pk}/")
async def tag(pk: int):
    return (
        await db_tag.get_tags(pk)
        or JSONResponse("NotFound", status.HTTP_404_NOT_FOUND)
    )


@recipe_router.post("/ingredients/")
async def create_ingredient(
    ingredient: schemas.Ingredient,
    user_dict: User = Depends(get_current_user)
):
    if user_dict["is_superuser"] or user_dict["is_staff"] == True:
        e = await db_ingredient.create_ingredient(ingredient)
        if type(e) != int:
            e = str(e).split(": ")[-1]
            return JSONResponse(f"Incorrect {e}", status.HTTP_400_BAD_REQUEST)
        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_403_FORBIDDEN)


@recipe_router.get("/ingredients/")
async def ingredients():
    return await db_ingredient.get_ingredient()


@recipe_router.get("/ingredients/{pk}/")
async def ingredient(pk: int):
    return (
        await db_ingredient.get_ingredient(pk)
        or JSONResponse("NotFound", status.HTTP_404_NOT_FOUND)
    )


@recipe_router.get("/recipes/")
async def пуе_recipe():
    return await query_list(await db_recipe.get_recipe_by_id(None))


@recipe_router.post("/recipes/")
async def create_recipe(
    text: str = Form(...),
    name: str = Form(...),
    image: UploadFile = File(...),
    cooking_time: int = Form(...),
    ingredients: list[schemas.AmountIngredient] = Body(...),
    tags: list[int] = Form(...),
    user_dict: User = Depends(get_current_user)
):

    filename = image.filename
    if not filename.lower().endswith(('.jpg', '.jpeg', 'bmp', 'png')):
        JSONResponse("NotFound", status.HTTP_404_NOT_FOUND)

    try:
        async with aiofiles.open(
            os.path.join(STATIC_ROOT, filename), "wb"
        ) as buffer:
            await buffer.write(await image.read())
        raise
    except Exception:
        buffer = os.path.join(STATIC_ROOT, filename)
        if os.path.isfile(buffer):
            os.remove(buffer)
        Response({"detail" "NotFound"}, status.HTTP_404_NOT_FOUND)

    print("====", name, text, filename, cooking_time, ingredients, tags)
    pk = await db_recipe.create_recipe(
        name, text, filename, cooking_time, ingredients, tags, user_dict["id"]
    )
    return await db_recipe.get_recipe_by_id(pk)


@recipe_router.get("/recipes/{pk}/")
async def recipes(pk: int):
    recipe_dict = await db_recipe.get_recipe_by_id(pk)
    if recipe_dict:
        return recipe_dict[0]
    return JSONResponse("Страница не найдена.", status.HTTP_404_NOT_FOUND)


@recipe_router.delete("/recipes/{pk}/")
async def delete_recipe(pk: int):
    return await db_recipe.delete_recipe(pk)
