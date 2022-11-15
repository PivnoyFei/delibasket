import os
from uuid import uuid4

import aiofiles
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Body, Depends, File, Form, UploadFile, status
from fastapi.responses import JSONResponse, Response, StreamingResponse
from starlette.requests import Request

from db import database
from recipes import schemas
from recipes.models import (FavoriteCart, Ingredient, Recipe, Tag, cart,
                            favorites)
from recipes.utils import (create_cart_favorite, create_tag_ingredient,
                           delete_cart_favorite)
from services import query_list
from settings import MEDIA_ROOT, NOT_AUTHENTICATED, NOT_FOUND
from users.models import User
from users.utils import get_current_user

router = APIRouter(prefix='/api', tags=["recipe"])
db_tag = Tag(database)
db_user = User(database)
db_recipe = Recipe(database)
db_ingredient = Ingredient(database)
db_favorite_cart = FavoriteCart(database)


@router.post("/tags/")
async def create_tag(tag: schemas.Tag, user: User = Depends(get_current_user)):
    return await create_tag_ingredient(db_tag.create_tag, tag, user)


@router.post("/ingredients/")
async def create_ingredient(
    ingredient: schemas.Ingredient, user: User = Depends(get_current_user)
):
    return await create_tag_ingredient(
        db_ingredient.create_ingredient, ingredient, user)


@router.get("/tags/", response_model=list[schemas.Tags])
@router.get("/tags/{pk}/", response_model=schemas.Tags)
@router.delete("/tags/{pk}/")
async def tags(
    request: Request, pk: int = None, user: User = Depends(get_current_user)
):
    if request.method == "DELETE":
        if user.is_superuser or user.is_staff is True:
            return await db_tag.delete_tag(pk)
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return await db_tag.get_tags(pk) or NOT_FOUND


@router.get("/ingredients/", response_model=list[schemas.Ingredients])
@router.get("/ingredients/{pk}/", response_model=schemas.Ingredients)
@router.delete("/ingredients/{pk}/")
async def ingredients(
    request: Request,
    name: str = None,
    pk: int = None,
    user: User = Depends(get_current_user)
):
    #if str(request.url).endswith(("tags")):
    #    db_model_delete = db_tag.delete_tag
    #    db_model_get = db_tag.get_tags
    #else:
    #    db_model_delete = db_ingredient.delete_ingredient
    #    db_model_get = db_ingredient.get_ingredient

    if request.method == "DELETE":
        if user.is_superuser or user.is_staff is True:
            return await db_ingredient.delete_ingredient(pk)
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return await db_ingredient.get_ingredient(pk, name) or NOT_FOUND


@router.post("/recipes/", response_model=schemas.Recipe)
async def create_recipe(
    request: Request,
    text: str = Form(...),
    name: str = Form(...),
    image: UploadFile = File(...),
    cooking_time: int = Form(...),
    ingredients: list[schemas.AmountIngredient] = Body(...),
    tags: list[int] = Form(...),
    user: User = Depends(get_current_user)
):

    if not user:
        return NOT_AUTHENTICATED
    for i in tags:
        if not await db_tag.get_tags(i):
            return JSONResponse(
                {"detail": f"Not tag {i}"}, status.HTTP_404_NOT_FOUND
            )
    for i in ingredients:
        if not await db_ingredient.get_ingredient(i.ingredient_id):
            return JSONResponse(
                {"detail": f"Not ingredient {i.ingredient_id}"},
                status.HTTP_404_NOT_FOUND
            )

    if not image.filename.lower().endswith(('.jpg', '.jpeg', '.bmp', '.png')):
        return JSONResponse(
            {"detail": "Invalid image format"}, status.HTTP_400_BAD_REQUEST)

    filename = f"{uuid4()}.{image.filename.split('.')[-1]}"
    try:
        async with aiofiles.open(
            os.path.join(MEDIA_ROOT, filename), "wb"
        ) as buffer:
            await buffer.write(await image.read())

            recipe_item = {
                "author_id": user.id,
                "name": name,
                "text": text,
                "image": filename,
                "cooking_time": cooking_time
            }
            pk = await db_recipe.create_recipe(
                recipe_item, ingredients, tags
            )
            r = await db_recipe.get_recipe_by_id(pk, user.id, request)
            return r[0]
    except (Exception, UniqueViolationError):
        buffer = os.path.join(MEDIA_ROOT, filename)
        if os.path.isfile(buffer):
            os.remove(buffer)
        return JSONResponse(
            {"detail": "Error image"}, status.HTTP_400_BAD_REQUEST)
    finally:
        image.file.close()


@router.get("/recipes/download_shopping_cart/")
async def download_shopping_cart(user: User = Depends(get_current_user)):
    if not user:
        return NOT_AUTHENTICATED
    ingredients = await db_favorite_cart.get_shopping_cart(user.id)
    file = os.path.join(MEDIA_ROOT, f'files/{user.username}.txt')
    try:
        with open(file, 'w', encoding="utf-8") as buffer:
            for item in ingredients:
                buffer.write(
                    f"{item.name} ({item.measurement_unit}) - {item.amount}\n"
                )
            return StreamingResponse(file, media_type='text/txt')
    except Exception:
        return {"message": "There was an error"}
    finally:
        os.remove(file)


@router.get("/recipes/", response_model=schemas.listRecipe)
@router.get("/recipes/{pk}/", response_model=schemas.Recipe)
@router.delete("/recipes/{pk}/", status_code=status.HTTP_204_NO_CONTENT)
async def recipes(
    request: Request, page, limit, is_favorited, pk: int = None, user: User = Depends(get_current_user)
):
    user_id = user.id if user else None
    if request.method == "DELETE":
        if not user_id:
            return NOT_AUTHENTICATED
        await db_recipe.delete_recipe(pk)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if pk:
        recipe_dict = await db_recipe.get_recipe_by_id(pk, user_id, request)
        return recipe_dict[0] if recipe_dict else NOT_FOUND

    return await query_list(await db_recipe.get_recipe_by_id(
        pk, user_id, request))


@router.delete("/recipes/{pk}/favorite/")
@router.delete("/recipes/{pk}/shopping_cart/")
@router.post("/recipes/{pk}/favorite/", response_model=schemas.Favorite)
@router.post("/recipes/{pk}/shopping_cart/", response_model=schemas.Favorite)
async def delete_cart(
    request: Request, pk: int, user: User = Depends(get_current_user)
):
    if not user:
            return NOT_AUTHENTICATED
    db_model = cart if str(request.url).endswith(("cart")) else favorites
    if request.method == "DELETE":
        return await delete_cart_favorite(pk, user, db_model)
    return await create_cart_favorite(request, pk, user, db_model)
