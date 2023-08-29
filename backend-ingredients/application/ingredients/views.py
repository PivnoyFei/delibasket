from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from application.auth.permissions import (
    IsAdmin,
    IsAuthenticated,
    PermissionsDependency,
)
from application.exceptions import NotFoundException
from application.ingredients.managers import IngredientManager
from application.ingredients.models import Ingredient
from application.ingredients.schemas import (
    AmountOut,
    IngredientCreate,
    IngredientOut,
    IngredientRecipeCreate,
    IngredientUpdate,
)
from application.managers import Manager
from application.schemas import SearchName

router = APIRouter()
admin_router = APIRouter()
ingredient = Manager(Ingredient)


@admin_router.post("/", response_model=IngredientOut, status_code=HTTP_200_OK)
async def create_ingredient(ingredient_in: IngredientCreate) -> JSONResponse:
    """Создавать ингредиенты может только администратор."""
    return await ingredient.create(ingredient_in.dict())


@router.get("/", response_model=list[IngredientOut], status_code=HTTP_200_OK)
async def get_ingredients(params: SearchName = Depends()) -> list:
    """Список ингредиентов с возможностью поиска по имени."""
    return await ingredient.get_all_list(
        params,
        attr_name="name",
        query_in=Ingredient.list_columns("id", "name", "measurement_unit"),
    )


recipe_router = APIRouter()


@recipe_router.post("/", response_model=None, status_code=HTTP_200_OK)
async def create_recipe_ingredient(ingredient_in: IngredientRecipeCreate) -> JSONResponse:
    """Сохранить ингредиенты для рецепта."""
    if await IngredientManager().create_amount_ingredient(ingredient_in):
        return JSONResponse({"detail": "OK"}, HTTP_200_OK)
    return JSONResponse({"detail": "BAD_REQUEST"}, HTTP_400_BAD_REQUEST)


@recipe_router.put("/", response_model=None, status_code=HTTP_200_OK)
async def update_recipe_ingredient(ingredient_in: IngredientRecipeCreate) -> JSONResponse:
    """Редактирвоать ингредиенты для рецепта."""
    if await IngredientManager().update_amount_ingredient(ingredient_in):
        return JSONResponse({"detail": "OK"}, HTTP_200_OK)
    return JSONResponse({"detail": "BAD_REQUEST"}, HTTP_400_BAD_REQUEST)


@recipe_router.get("/shopping_cart/", response_model=list[AmountOut], status_code=HTTP_200_OK)
async def get_shopping_cart(in_recipes: list[int]) -> JSONResponse:
    """Редактирвоать ингредиенты для рецепта."""
    ingredients = await IngredientManager().get_shopping_cart(in_recipes)
    return ingredients or JSONResponse({"detail": "BAD_REQUEST"}, HTTP_400_BAD_REQUEST)


@recipe_router.get("/{recipe_id}/", response_model=list[AmountOut], status_code=HTTP_200_OK)
async def get_recipe_ingredient(recipe_id: int) -> JSONResponse:
    """Удалить ингредиенты для рецепта."""
    ingredients = await IngredientManager().get_amount_ingredient(recipe_id)
    return ingredients or JSONResponse({"detail": "BAD_REQUEST"}, HTTP_400_BAD_REQUEST)


@recipe_router.delete("/{recipe_id}/", response_model=None, status_code=HTTP_200_OK)
async def delete_recipe_ingredient(recipe_id: int) -> JSONResponse:
    """Удалить ингредиенты для рецепта."""
    if await IngredientManager().delete_amount_ingredient(recipe_id):
        return JSONResponse({"detail": "OK"}, HTTP_200_OK)
    return JSONResponse({"detail": "BAD_REQUEST"}, HTTP_400_BAD_REQUEST)


router.include_router(
    recipe_router,
    prefix="/recipe",
    tags=["recipe"],
)


@router.get("/{ingredient_id}/", response_model=IngredientOut, status_code=HTTP_200_OK)
async def details_ingredient(ingredient_id: int) -> Any:
    """Уникальный идентификатор этого ингредиента."""
    if result := await ingredient.by_id(pk=ingredient_id):
        return result
    raise NotFoundException


@router.patch(
    "/{ingredient_id}/",
    response_model=IngredientOut,
    dependencies=[Depends(PermissionsDependency([IsAuthenticated, IsAdmin]))],
    status_code=HTTP_200_OK,
)
async def update_ingred(ingredient_id: int, ingredient_in: IngredientUpdate) -> JSONResponse:
    """Редактировать ингредиенты может только администратор."""
    items = {k: v for k, v in ingredient_in.dict().items() if v}
    return await ingredient.update(items=items, pk=ingredient_id)


@router.delete(
    "/{ingredient_id}/",
    dependencies=[Depends(PermissionsDependency([IsAuthenticated, IsAdmin]))],
    status_code=HTTP_200_OK,
)
async def delete_ingredient(ingredient_id: int) -> JSONResponse:
    if not await ingredient.delete(pk=ingredient_id):
        raise NotFoundException("Ингредиент не существует")
