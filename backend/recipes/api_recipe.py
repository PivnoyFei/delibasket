import os

import aiofiles
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.background import BackgroundTask
from starlette.requests import Request

from db import database
from recipes.models import (FavoriteCart, Ingredient, Recipe, Tag, cart,
                            favorites)
from recipes.schemas import (SFavorite, SIngredient, SIngredients, SlistRecipe,
                             SLoadRecipe, SPatchRecipe, SRecipe, STag, STags)
from recipes.utils import (QueryParams, base64_image, check_ingredient,
                           check_tags, create_cart_favorite,
                           delete_cart_favorite, utils_tag_ingredient)
from services import image_delete, query_list
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
async def create_tag(tag: STag, user: User = PROTECTED):
    """ Создавать теги может только администратор. """
    return await utils_tag_ingredient(db_tag.create_tag, tag, user)


@router.post("/ingredients/")
async def create_ingredient(ingredient: SIngredient, user: User = PROTECTED):
    """ Создавать ингредиенты может только администратор. """
    return await utils_tag_ingredient(
        db_ingredient.create_ingredient, ingredient, user)


@router.post("/tag/{pk}/", response_model=STags)
async def update_tag(tag: STag, pk: str, user: User = PROTECTED):
    """ Редактировать теги может только администратор. """
    return await utils_tag_ingredient(db_tag.update_tag, tag, user, pk)


@router.post("/ingredient/{pk}/", response_model=SIngredients)
async def update_ingred(ingred: SIngredient, pk: int, user: User = PROTECTED):
    """ Редактировать ингредиенты может только администратор. """
    return await utils_tag_ingredient(
        db_ingredient.update_ingredient, ingred, user, pk)


@router.get("/tags/", response_model=list[STags])
@router.get("/ingredients/", response_model=list[SIngredients])
@router.get("/tags/{pk}/", response_model=STags)
@router.get("/ingredients/{pk}/", response_model=SIngredients)
@router.delete("/tags/{pk}/")
@router.delete("/ingredients/{pk}/")
async def tags_ingredients(
    request: Request,
    name: str = None,
    pk: int = None,
    user: User = PROTECTED
):
    """
    /tags/ или /ingredients/ - выдает список тегов/ингредиентов,
    query параметр name= выдает тег/ингредиент по имени.
    /tags/{pk}/ или /ingredients/{pk}/ - выдает тег/ингредиент по id.
    Удалять ингредиенты и теги может только администратор.
    """
    if "tags" in str(request.url.path):
        db_model_delete = db_tag.delete_tag
        db_model_get = db_tag.get_tags
    else:
        db_model_delete = db_ingredient.delete_ingredient
        db_model_get = db_ingredient.get_ingredient

    if request.method == "DELETE":
        if user.is_staff or user.is_superuser:
            return await db_model_delete(pk)
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return await db_model_get(pk, name) or NOT_FOUND


@router.post("/recipes/", response_model=SRecipe)
async def create_recipe(
    request: Request, recipe: SLoadRecipe, user: User = PROTECTED
):
    """ Создает рецепт. Картинка в фронтенда поступает в формате base64. """
    if not user:
        return NOT_AUTHENTICATED
    await check_tags(recipe.tags)
    await check_ingredient(recipe.ingredients)
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
        r = await db_recipe.get_recipe(pk, user_id=user.id, request=request)
        return r[0]
    except (Exception, UniqueViolationError):
        await image_delete(image_path=image_path)
        return JSONResponse(
            {"detail": "Error recipe"}, status.HTTP_400_BAD_REQUEST)


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


@router.get("/recipes/", response_model=SlistRecipe)
@router.get("/recipes/{pk}/", response_model=SRecipe)
@router.delete("/recipes/{pk}/", status_code=status.HTTP_204_NO_CONTENT)
async def recipes(
    request: Request,
    pk: int = None,
    page: int = None,
    limit: int = None,
    author: int = None,
    is_favorited: int = None,
    is_in_shopping_cart: int = None,
    user: User = PROTECTED,
    tags: QueryParams = Depends(QueryParams),
):
    """
    Получить все рецепты, один, удалить рецепт.
    Администратор может удалять любые рецепты.
    """
    user_id = user.id if user else None
    if request.method == "DELETE":
        if not user_id:
            return NOT_AUTHENTICATED
        recipe = await db_recipe.check_recipe_by_id(pk)
        if recipe.author_id == user.id or user.is_staff or user.is_superuser:
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
        user_id=user_id, author=author, is_in_cart=is_in_cart, request=request
    )
    if recipe_dict:
        count = await db_recipe.count_recipe(
            author, tags, is_favorited, is_in_cart
        )
        return await query_list(recipe_dict, request, count, page, limit)
    return await query_list(recipe_dict, request, 0, page, limit)


@router.patch("/recipes/{pk}/", response_model=SRecipe)
async def update_recipe(
    request: Request, pk: int, recipe: SPatchRecipe, user: User = PROTECTED
):
    """
    Перед редактированием рецепта, фронтенд получает данные рецепта
    и после изменения пользователем отправляет сюда.
    """
    if not user:
        return NOT_AUTHENTICATED
    author = await db_recipe.check_recipe_image_by_id(pk)
    if author.author_id == user.id or user.is_staff or user.is_superuser:
        await check_tags(recipe.tags)
        await check_ingredient(recipe.ingredients)
        if recipe.image:
            filename, image_path = await base64_image(recipe.image)
            await image_delete(filename=author.image)
        else:
            filename, image_path = author.image, ""
        try:
            recipe_item = {
                "author_id": author.author_id,
                "name": recipe.name,
                "text": recipe.text,
                "image": filename
            }
            pk = await db_recipe.update_recipe(
                pk, recipe_item, recipe.ingredients, recipe.tags
            )
            result = await db_recipe.get_recipe(
                pk, user_id=user.id, request=request)
            return result[0]

        except UniqueViolationError as e:
            await image_delete(filename, image_path)
            return JSONResponse(
                {"detail": e}, status.HTTP_400_BAD_REQUEST)

    return Response(status_code=status.HTTP_403_FORBIDDEN)


@router.post("/recipes/{pk}/favorite/", response_model=SFavorite)
@router.delete("/recipes/{pk}/favorite/")
@router.post("/recipes/{pk}/shopping_cart/", response_model=SFavorite)
@router.delete("/recipes/{pk}/shopping_cart/")
async def delete_cart(request: Request, pk: int, user: User = PROTECTED):
    """ Обрабатывает запросы подписки на рецепты и добавления в корзину. """
    if not user:
        return NOT_AUTHENTICATED
    db_model = favorites if "favorite" in str(request.url.path) else cart
    if request.method == "DELETE":
        return await delete_cart_favorite(pk, user, db_model)
    return await create_cart_favorite(request, pk, user, db_model)
