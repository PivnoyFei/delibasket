from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK

from application.auth.permissions import IsAdmin, IsAuthenticated, PermissionsDependency
from application.exceptions import NotFoundException
from application.managers import Manager
from application.schemas import SearchName
from application.tags.models import Tag
from application.tags.schemas import TagCreate, TagOut, TagUpdate

router = APIRouter()
admin_router = APIRouter()
tag = Manager(Tag)


@admin_router.post("/", status_code=HTTP_200_OK)
async def create_tag(tag_in: TagCreate) -> JSONResponse:
    """Создавать теги может только администратор."""
    return await tag.create(tag_in.dict())


@router.get("/", response_model=list[TagOut], status_code=HTTP_200_OK)
async def get_tags(params: SearchName = Depends()) -> list:
    """Cписок тегов."""
    return await tag.get_all_list(
        params,
        attr_name="name",
        query_in=Tag.list_columns("id", "name", "color", "slug"),
    )


@router.get("/{tag_id}/", response_model=TagOut, status_code=HTTP_200_OK)
async def details_tag(tag_id: int) -> Any:
    """Получение тега."""
    if result := await tag.by_id(pk=tag_id):
        return result
    raise NotFoundException


@admin_router.patch("/{tag_id}/", response_model=TagOut, status_code=HTTP_200_OK)
async def update_tag(tag_id: int, tag_in: TagUpdate) -> JSONResponse:
    """Редактировать теги может только администратор."""
    items = {k: v for k, v in tag_in.dict().items() if v}
    return await tag.update(items=items, pk=tag_id)


@admin_router.delete("/{tag_id}/", status_code=HTTP_200_OK)
async def delete_tag(tag_id: int) -> JSONResponse:
    if not await tag.delete(pk=tag_id):
        raise NotFoundException("Тег не существует")


router.include_router(
    admin_router,
    dependencies=[Depends(PermissionsDependency([IsAuthenticated, IsAdmin]))],
)
