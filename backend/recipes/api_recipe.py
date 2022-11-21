import os

import aiofiles
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.background import BackgroundTask
from starlette.requests import Request

from db import database
from recipes import schemas
from recipes.models import (FavoriteCart, Ingredient, Recipe, Tag, cart,
                            favorites)
from recipes.utils import (QueryParams, base64_image, create_cart_favorite,
                           create_tag_ingredient, delete_cart_favorite)
from services import query_list
from settings import FILES_ROOT, NOT_AUTHENTICATED, NOT_FOUND
from users.models import User
from users.utils import get_current_user

router = APIRouter(prefix='/api', tags=["recipe"])
PROTECTED = Depends(get_current_user)
db_tag = Tag(database)
db_recipe = Recipe(database)
db_ingredient = Ingredient(database)
db_favorite_cart = FavoriteCart(database)


@router.post("/tags/")
async def create_tag(tag: schemas.Tag, user: User = PROTECTED):
    return await create_tag_ingredient(db_tag.create_tag, tag, user)


@router.post("/ingredients/")
async def create_ingredient(
    ingredient: schemas.Ingredient, user: User = PROTECTED
):
    return await create_tag_ingredient(
        db_ingredient.create_ingredient, ingredient, user)


@router.get("/tags/", response_model=list[schemas.Tags])
@router.get("/ingredients/", response_model=list[schemas.Ingredients])
@router.get("/tags/{pk}/", response_model=schemas.Tags)
@router.get("/ingredients/{pk}/", response_model=schemas.Ingredients)
@router.delete("/tags/{pk}/")
@router.delete("/ingredients/{pk}/")
async def ingredients(
    request: Request,
    name: str = None,
    pk: int = None,
    user: User = PROTECTED
):
    if "tags" in str(request.url.path):
        db_model_delete = db_tag.delete_tag
        db_model_get = db_tag.get_tags
    else:
        db_model_delete = db_ingredient.delete_ingredient
        db_model_get = db_ingredient.get_ingredient

    if request.method == "DELETE":
        if user.is_superuser or user.is_staff is True:
            return await db_model_delete(pk)
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return await db_model_get(pk, name) or NOT_FOUND


@router.post("/recipes/", response_model=schemas.Recipe)
async def create_recipe(
    request: Request,
    recipe: schemas.LoadRecipe,
    user: User = PROTECTED
):
    if not user:
        return NOT_AUTHENTICATED
    for i in recipe.tags:
        if not await db_tag.get_tags(i):
            return JSONResponse(
                {"detail": f"Not tag {i}"}, status.HTTP_404_NOT_FOUND
            )
    for i in recipe.ingredients:
        i = i["id"]
        if not await db_ingredient.get_ingredient(i):
            return JSONResponse(
                {"detail": f"Not ingredient {i}"}, status.HTTP_404_NOT_FOUND
            )
    filename, image_path = await base64_image(recipe.image)
    try:
        recipe_item = {
            "author_id": user.id,
            "name": recipe.name,
            "text": recipe.text,
            "image": filename,
            "cooking_time": recipe.cooking_time
        }
        pk = await db_recipe.create_recipe(
            recipe_item, recipe.ingredients, recipe.tags
        )
        print("pk", pk)
        r = await db_recipe.get_recipe(pk, user_id=user.id, request=request)
        return r[0]
    except (Exception, UniqueViolationError):
        if os.path.isfile(image_path):
            os.remove(image_path)
        return JSONResponse(
            {"detail": "Error image"}, status.HTTP_400_BAD_REQUEST)


@router.get("/recipes/download_shopping_cart/")
async def download_shopping_cart(user: User = PROTECTED):
    """
    Список покупок скачивается в формате .txt.
    Пользователь получает файл с суммированным перечнем
    и количеством необходимых ингредиентов для всех рецептов.
    """
    def cleanup():
        if os.path.isfile(file_path):
            os.remove(file_path)

    if not user:
        return NOT_AUTHENTICATED
    ingredients = await db_favorite_cart.get_shopping_cart(user.id)
    if not ingredients:
        return JSONResponse(
            {"detail": "No recipes in cart"}
        )
    filename = f'{user.username}.txt'
    file_path = os.path.join(FILES_ROOT, filename)
    ingredients_set = {}
    for item in ingredients:
        if item not in ingredients_set:
            ingredients_set[item.name] = {
                'amount': item.amount,
                'measurement_unit': item.measurement_unit,
            }
        else:
            ingredients_set[item.name]['amount'] += item.amount

    cart_list = ['{} - {} {}.\n'.format(
        name, ingredients_set[name]['amount'],
        ingredients_set[name]['measurement_unit'],
    ) for name in ingredients_set]

    async with aiofiles.open(file_path, 'w', encoding="utf-8") as buffer:
        await buffer.write("".join(cart_list))
    return FileResponse(file_path, background=BackgroundTask(cleanup))


@router.get("/recipes/", response_model=schemas.listRecipe)
@router.get("/recipes/{pk}/", response_model=schemas.Recipe)
@router.delete("/recipes/{pk}/", status_code=status.HTTP_204_NO_CONTENT)
async def recipes(
    request: Request,
    pk: int = None,
    page: int = None,
    limit: int = None,
    is_favorited: int = None,
    is_in_shopping_cart: int = None,
    user: User = PROTECTED,
    tags: QueryParams = Depends(QueryParams),
):
    user_id = user.id if user else None
    if request.method == "DELETE":
        if not user_id:
            return NOT_AUTHENTICATED
        await db_recipe.delete_recipe(pk)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if pk:
        recipe_dict = await db_recipe.get_recipe(
            pk=pk, user_id=user_id, request=request)
        return recipe_dict[0] if recipe_dict else NOT_FOUND

    is_favorited = False if is_favorited and user_id else True
    is_in_cart = False if is_in_shopping_cart and user_id else True

    recipe_dict = await db_recipe.get_recipe(
        pk=pk, tags=tags, page=page, limit=limit, is_favorited=is_favorited,
        user_id=user_id, is_in_cart=is_in_cart, request=request
    )
    if recipe_dict:
        count = await db_recipe.count_recipe(tags, is_favorited, is_in_cart)
        return await query_list(recipe_dict, request, count, page, limit)
    return await query_list(recipe_dict, request, 0, page, limit)


@router.post("/recipes/{pk}/favorite/", response_model=schemas.Favorite)
@router.delete("/recipes/{pk}/favorite/")
@router.post("/recipes/{pk}/shopping_cart/", response_model=schemas.Favorite)
@router.delete("/recipes/{pk}/shopping_cart/")
async def delete_cart(request: Request, pk: int, user: User = PROTECTED):
    if not user:
        return NOT_AUTHENTICATED
    db_model = favorites if "favorite" in str(request.url.path) else cart
    if request.method == "DELETE":
        return await delete_cart_favorite(pk, user, db_model)
    return await create_cart_favorite(request, pk, user, db_model)
