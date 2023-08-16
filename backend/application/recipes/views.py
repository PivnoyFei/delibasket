import logging
import os
from typing import Any

import aiofiles
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from application.auth.permissions import IsAuthenticated, IsAvtor, PermissionsDependency
from application.exceptions import BadRequestException, NotFoundException
from application.managers import Manager
from application.recipes.managers import FavoriteCartManager, RecipeManager
from application.recipes.models import Cart, Favorite, Recipe
from application.recipes.schemas import CreateRecipe, RecipeOut, UpdateRecipe
from application.recipes.utils import base64_image
from application.schemas import Result, SearchRecipe
from application.services import image_delete
from application.settings import FILES_ROOT

router = APIRouter()
favorite = FavoriteCartManager(Favorite)
cart = FavoriteCartManager(Cart)


@router.post(
    "/",
    response_model=RecipeOut,
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    response_description="Рецепт успешно создан",
    status_code=HTTP_201_CREATED,
)
async def create_recipe(request: Request, recipe_in: CreateRecipe) -> JSONResponse:
    """Создание рецепта.<br>
    Доступно только авторизованному пользователю.<br>
    Картинка в фронтенда поступает в формате base64."""
    filename, image_path = await base64_image(recipe_in.image)
    try:
        items = await recipe_in.to_dict(request.user.id, filename)
        recipe_id = await RecipeManager().create(items, recipe_in)

    except (Exception, UniqueViolationError) as e:
        await image_delete(image_path=image_path)
        logging.error(e)
        raise BadRequestException("Ошибка создания рецепта")

    if recipe_id:
        return await RecipeManager().get(request, recipe_id)
    raise NotFoundException


@router.get("/", response_model=Result[RecipeOut], status_code=HTTP_200_OK)
async def get_recipes(request: Request, params: SearchRecipe = Depends()) -> JSONResponse:
    """Список рецептов.<br>
    Страница доступна всем пользователям.<br>
    Доступна фильтрация по избранному, автору, списку покупок и тегам."""
    user_id = request.user.id

    if (params.is_favorited or params.is_in_shopping_cart) and not user_id:
        raise BadRequestException(
            "Доступна фильтрация по избранному и списку покупок "
            "доступна только авторизованному пользователю"
        )

    params.is_favorited = False if params.is_favorited and user_id else True
    params.is_in_shopping_cart = False if params.is_in_shopping_cart and user_id else True

    count, result = await RecipeManager().get_all(request, params)
    return await Result.result(request.url, count, params, result)


@router.get(
    "/download_shopping_cart/",
    response_model=None,
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_200_OK,
)
async def download_shopping_cart(request: Request) -> FileResponse | JSONResponse:
    """Скачать файл со списком покупок.<br>
    Это может быть TXT/PDF/CSV.<br>
    Пользователь получает файл с суммированным перечнем <br>
    и количеством необходимых ингредиентов для всех рецептов.<br>
    Доступно только авторизованным пользователям.
    """

    def cleanup() -> None:
        if os.path.isfile(file_path):
            os.remove(file_path)

    if ingredients := await FavoriteCartManager.get_shopping_cart(request.user.id):
        ingredients_set = {}
        for item in ingredients:
            if item not in ingredients_set:
                ingredients_set[item.name] = {
                    "amount": item.amount,
                    "measurement_unit": item.measurement_unit,
                }
            else:
                ingredients_set[item.name]["amount"] += item.amount

        cart_list = [
            "{} - {} {}.\n".format(
                name,
                ingredients_set[name]["amount"],
                ingredients_set[name]["measurement_unit"],
            )
            for name in ingredients_set
        ]
        file_path = os.path.join(FILES_ROOT, f"{request.user.username}.txt")
        try:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as buffer:
                await buffer.write("".join(cart_list))

        except Exception as e:
            logging.error(e)
            raise BadRequestException("Не удалось загрузить корзину")
        return FileResponse(file_path, background=BackgroundTask(cleanup))
    raise NotFoundException


@router.get("/{recipe_id}/", response_model=RecipeOut, status_code=HTTP_200_OK)
async def get_recipe(request: Request, recipe_id: int) -> Any:
    """Получение рецепта."""
    if result := await RecipeManager().get(request, recipe_id):
        return result
    raise NotFoundException


@router.patch(
    "/{recipe_id}/",
    response_model=RecipeOut,
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_200_OK,
)
async def update_recipe(request: Request, recipe_id: int, recipe_in: UpdateRecipe) -> JSONResponse:
    """Обновление рецепта.<br>
    Доступно только автору данного рецепта <br>
    Перед редактированием рецепта, фронт получает данные рецепта <br>
    и после изменения пользователем отправляет сюда.
    """

    recipe: Recipe | None = await Manager(Recipe).by_id(recipe_id)
    if not recipe:
        raise NotFoundException

    if await IsAvtor().caxtom_has_permission(request, recipe.author_id):
        if recipe_in.image:
            filename, image_path = await base64_image(recipe_in.image)
            items = await recipe_in.to_dict(recipe, filename)
        else:
            items = await recipe_in.to_dict(recipe)

        try:
            if await RecipeManager().update(recipe_id, items, recipe_in):
                return JSONResponse({"detail": "Рецепт успешно обновлен"}, HTTP_200_OK)

        except Exception as e:
            logging.error(e)
            if recipe_in.image:
                await image_delete(filename, image_path)

        finally:
            if recipe_in.image:
                await image_delete(filename=recipe.image)

    raise BadRequestException("При обновлении рецепта произошла ошибка")


@router.delete(
    "/{recipe_id}/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_recipe(request: Request, recipe_id: int) -> JSONResponse:
    """Удаление рецепта. Доступно только автору данного рецепта"""
    author_id = await RecipeManager().author_by_id(recipe_id)
    if not author_id:
        raise NotFoundException

    if await IsAvtor().caxtom_has_permission(request, author_id):
        if await Manager(Recipe).delete(recipe_id):
            return Response(status_code=HTTP_204_NO_CONTENT)

    raise BadRequestException("При удалении рецепта произошла ошибка")


@router.post(
    "/{recipe_id}/favorite/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_201_CREATED,
)
async def create_favorite(request: Request, recipe_id: int) -> JSONResponse:
    """Добавить рецепт в избранное. Доступно только авторизованному пользователю."""
    if await favorite.create(request, recipe_id, request.user.id):
        return JSONResponse({"detail": "Рецепт успешно добавлен в избранное"}, HTTP_201_CREATED)

    raise BadRequestException(
        "Ошибка добавления в избранное (Например, когда рецепт уже есть в избранном)"
    )


@router.delete(
    "/{recipe_id}/favorite/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_favorite(request: Request, recipe_id: int) -> JSONResponse:
    """Удалить рецепт из избранного. <br>Доступно только авторизованным пользователям."""
    if await favorite.delete(recipe_id, request.user.id):
        return Response(status_code=HTTP_204_NO_CONTENT)

    raise BadRequestException("Ошибка удаления из избранного (Например, когда рецепта там не было)")


@router.post(
    "/{recipe_id}/shopping_cart/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_201_CREATED,
)
async def create_cart(request: Request, recipe_id: int) -> JSONResponse:
    """Добавить рецепт в список покупок. Доступно только авторизованным пользователям."""
    if await cart.create(request, recipe_id, request.user.id):
        return JSONResponse(
            {"detail": "Рецепт успешно добавлен в список покупок"},
            HTTP_201_CREATED,
        )

    raise BadRequestException(
        "Ошибка добавления в список покупок " "(Например, когда рецепт уже есть в списке покупок)"
    )


@router.delete(
    "/{recipe_id}/shopping_cart/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated]))],
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_cart(request: Request, recipe_id: int) -> JSONResponse:
    """Удалить рецепт из списка покупок. Доступно только авторизованным пользователям."""
    if await cart.delete(recipe_id, request.user.id):
        return Response(status_code=HTTP_204_NO_CONTENT)

    raise BadRequestException(
        "Ошибка удаления из списка покупок (Например, когда рецепта там не было)"
    )
