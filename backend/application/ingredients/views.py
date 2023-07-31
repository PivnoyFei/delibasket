from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK

from application.auth.permissions import IsAdmin, IsAuthenticated, PermissionsDependency
from application.exceptions import NotFoundException
from application.ingredients.models import Ingredient
from application.ingredients.schemas import IngredientCreate, IngredientOut, IngredientUpdate
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


@router.get("/{ingredient_id}/", response_model=IngredientOut, status_code=HTTP_200_OK)
async def details_ingredient(ingredient_id: int) -> Any:
    """Уникальный идентификатор этого ингредиента."""
    if result := await ingredient.by_id(pk=ingredient_id):
        return result
    raise NotFoundException


@admin_router.patch("/{ingredient_id}/", response_model=IngredientOut, status_code=HTTP_200_OK)
async def update_ingred(ingredient_id: int, ingredient_in: IngredientUpdate) -> JSONResponse:
    """Редактировать ингредиенты может только администратор."""
    items = {k: v for k, v in ingredient_in.dict().items() if v}
    return await ingredient.update(items=items, pk=ingredient_id)


@admin_router.delete("/{ingredient_id}/", status_code=HTTP_200_OK)
async def delete_ingredient(ingredient_id: int) -> JSONResponse:
    if not await ingredient.delete(pk=ingredient_id):
        raise NotFoundException("Ингредиент не существует")


router.include_router(
    admin_router,
    dependencies=[Depends(PermissionsDependency([IsAuthenticated, IsAdmin]))],
)
