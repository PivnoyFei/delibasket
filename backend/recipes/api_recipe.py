import os
from typing import Any

import aiofiles
from asyncpg.exceptions import UniqueViolationError
from db import get_session
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse, JSONResponse, Response
from recipes.models import (Cart, Favorite, FavoriteCartDB, IngredientDB,
                            RecipeDB, TagDB)
from recipes.schemas import (CreateRecipe, FavoriteOut, IngredientOut,
                             PatchRecipe, QueryParams, RecipeOut, SIngredient,
                             STag, TagOut, listRecipe)
from recipes.utils import (base64_image, create_cart_favorite,
                           delete_cart_favorite, tag_ingredient)
from services import image_delete, query_list
from settings import FILES_ROOT, NOT_AUTHENTICATED, NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask
from starlette.requests import Request
from users.models import User
from users.utils import get_current_user

router = APIRouter(prefix='/api', tags=["recipe"])
PROTECTED = Depends(get_current_user)
SESSION = Depends(get_session)


@router.post("/tags/", status_code=status.HTTP_200_OK)
async def create_tag(tag: STag, user: User = PROTECTED, session: AsyncSession = SESSION) -> JSONResponse:
    """ Создавать теги может только администратор. """
    return await tag_ingredient(session, TagDB.create, tag, user)


@router.post("/ingredients/", response_model=IngredientOut, status_code=status.HTTP_200_OK)
async def create_ingredient(
    ingredient: SIngredient,
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> JSONResponse:
    """ Создавать ингредиенты может только администратор. """
    return await tag_ingredient(session, IngredientDB.create, ingredient, user)


@router.patch("/tags/{pk}/", response_model=TagOut, status_code=status.HTTP_200_OK)
async def update_tag(
    tag: STag,
    pk: int,
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> JSONResponse:
    """ Редактировать теги может только администратор. """
    return await tag_ingredient(session, TagDB.update, tag, user, pk)


@router.patch("/ingredients/{pk}/", response_model=IngredientOut, status_code=status.HTTP_200_OK)
async def update_ingred(
    ingredient: SIngredient,
    pk: int,
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> JSONResponse:
    """ Редактировать ингредиенты может только администратор. """
    return await tag_ingredient(session, IngredientDB.update, ingredient, user, pk)


@router.get("/tags/", response_model=list[TagOut], status_code=status.HTTP_200_OK)
@router.get("/ingredients/", response_model=list[IngredientOut], status_code=status.HTTP_200_OK)
@router.get("/tags/{pk}/", response_model=TagOut, status_code=status.HTTP_200_OK)
@router.get("/ingredients/{pk}/", response_model=IngredientOut, status_code=status.HTTP_200_OK)
@router.delete("/tags/{pk}/", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/ingredients/{pk}/", status_code=status.HTTP_204_NO_CONTENT)
async def tags_ingredients(
    request: Request,
    name: str = Query(None),
    pk: int | None = None,
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> Any:
    """
    /tags/ или /ingredients/ - выдает список тегов/ингредиентов,
    query параметр name= выдает тег/ингредиент по имени.
    /tags/{pk}/ или /ingredients/{pk}/ - выдает тег/ингредиент по id.
    Удалять ингредиенты и теги может только администратор.
    """
    if "tags" in str(request.url.path):
        db_model_delete = TagDB.delete
        db_model_get = TagDB.get
    else:
        db_model_delete = IngredientDB.delete
        db_model_get = IngredientDB.get

    if request.method == "DELETE" and pk:
        if user.is_staff or user.is_superuser:
            return await db_model_delete(session, pk)
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return await db_model_get(session, pk, name) or NOT_FOUND


@router.post("/recipes/", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    request: Request,
    recipe: CreateRecipe,
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> Any:
    """ Создает рецепт. Картинка в фронтенда поступает в формате base64. """
    if not user:
        return NOT_AUTHENTICATED
    filename, image_path = await base64_image(recipe.image)

    try:
        recipe_item = {
            "author_id": user.id,
            "name": recipe.name,
            "text": recipe.text,
            "image": filename,
            "cooking_time": recipe.cooking_time
        }
        pk = await RecipeDB.create(
            session, recipe_item, recipe.ingredients, recipe.tags
        )
        if result := await RecipeDB.get(session, request, pk, user_id=user.id):
            return result[0]

    except (Exception, UniqueViolationError):
        await image_delete(image_path=image_path)
        return JSONResponse(
            {"detail": "Error recipe"}, status.HTTP_400_BAD_REQUEST)


@router.get("/recipes/download_shopping_cart/", status_code=status.HTTP_200_OK)
async def download_shopping_cart(
    user: User = PROTECTED, session: AsyncSession = SESSION
) -> FileResponse | JSONResponse:
    """
    Список покупок скачивается в формате .txt.
    Пользователь получает файл с суммированным перечнем
    и количеством необходимых ингредиентов для всех рецептов.
    """
    def cleanup() -> None:
        if os.path.isfile(file_path):
            os.remove(file_path)

    if not user:
        return NOT_AUTHENTICATED
    ingredients = await FavoriteCartDB.get_shopping_cart(session, user.id)

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


@router.get("/recipes/", response_model=listRecipe, status_code=status.HTTP_200_OK)
@router.get("/recipes/{pk}/", response_model=RecipeOut, status_code=status.HTTP_200_OK)
@router.delete("/recipes/{pk}/", status_code=status.HTTP_204_NO_CONTENT)
async def recipes(
    request: Request,
    pk: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(6, ge=1),
    author: int | None = Query(None),
    is_favorited: int | None = Query(None),
    is_in_shopping_cart: int | None = Query(None),
    user: User = PROTECTED,
    tags: QueryParams = Depends(QueryParams),
    session: AsyncSession = SESSION,
) -> Any:
    """
    Получить все рецепты, один, удалить рецепт.
    Администратор может удалять любые рецепты.
    """
    user_id = user.id if user else None

    if request.method == "DELETE" and pk:
        if not user_id:
            return NOT_AUTHENTICATED
        author_id = await RecipeDB.check_author_by_id(session, pk)
        if author_id == user.id or user.is_staff or user.is_superuser:
            await RecipeDB.delete(session, pk)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if pk:
        recipe_dict = await RecipeDB.get(
            session, request, pk=pk, user_id=user_id)
        return recipe_dict[0] if recipe_dict else NOT_FOUND

    is_favorited = False if is_favorited and user_id else True
    is_in_cart = False if is_in_shopping_cart and user_id else True

    recipe_dict = await RecipeDB.get(
        session, request, pk=pk, tags=tags, page=page, limit=limit,
        is_favorited=is_favorited, user_id=user_id, author=author, is_in_cart=is_in_cart
    )
    if recipe_dict:
        count = await RecipeDB.count_recipe(
            session, author, tags, is_favorited, is_in_cart
        )
        return await query_list(recipe_dict, request, count, page, limit)
    return await query_list([], request, 0, page, limit)


@router.patch("/recipes/{pk}/", response_model=RecipeOut, status_code=status.HTTP_200_OK)
async def update_recipe(
    request: Request,
    pk: int,
    recipe: PatchRecipe,
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> Any:
    """
    Перед редактированием рецепта, фронтенд получает данные рецепта
    и после изменения пользователем отправляет сюда.
    """
    if not user:
        return NOT_AUTHENTICATED
    author = await RecipeDB.check_recipe_author_image_by_id(session, pk)
    if author.author_id == user.id or user.is_staff or user.is_superuser:
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
            recipe_id = await RecipeDB.update(
                session, pk, recipe_item, recipe.ingredients, recipe.tags
            )
            if result := await RecipeDB.get(session, request, recipe_id, user_id=user.id):
                return result[0]

        except:
            await image_delete(filename, image_path)
            return JSONResponse(
                {"detail": "error"}, status.HTTP_400_BAD_REQUEST)

    return Response(status_code=status.HTTP_403_FORBIDDEN)


@router.post("/recipes/{pk}/favorite/", response_model=FavoriteOut, status_code=status.HTTP_200_OK)
@router.delete("/recipes/{pk}/favorite/", status_code=status.HTTP_204_NO_CONTENT)
@router.post("/recipes/{pk}/shopping_cart/", response_model=FavoriteOut, status_code=status.HTTP_200_OK)
@router.delete("/recipes/{pk}/shopping_cart/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cart(
    request: Request,
    pk: int,
    user: User = PROTECTED,
    session: AsyncSession = SESSION,
) -> JSONResponse | list[FavoriteOut]:
    """ Обрабатывает запросы подписки на рецепты и добавления в корзину. """
    if not user:
        return NOT_AUTHENTICATED
    db_model = Favorite if "favorite" in str(request.url.path) else Cart
    if request.method == "DELETE":
        return await delete_cart_favorite(pk, user, db_model, session)
    return await create_cart_favorite(request, pk, user, db_model, session)
