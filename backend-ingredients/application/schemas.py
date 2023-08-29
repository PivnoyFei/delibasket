from typing import Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, select
from sqlalchemy.sql import func

from application.settings import PAGINATION_SIZE

name_str = "^([А-Яа-я]+|[A-Za-z]+)$"
name_en_str = "^[A-Za-z]+$"

_TS = TypeVar("_TS")
_TM = TypeVar("_TM")


class BaseSchema(BaseModel):
    id: int

    class ConfigDict:
        from_attributes = True


class Params(BaseModel):
    page: int = Query(1, ge=1, description="Номер страницы.")
    limit: int = Query(
        PAGINATION_SIZE,
        ge=1,
        le=1000,
        description="Количество объектов на странице.",
    )

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    def has_next(self, count: int) -> bool:
        next_page = (self.page + 1) * self.limit
        return next_page <= count or next_page - count < self.limit

    async def search(self) -> Select:
        raise NotImplementedError("Метод должен быть переопределен.")

    @staticmethod
    async def count(model: Sequence[_TM]) -> Select:
        return select(func.count(model.id).label("is_count"))

    async def limit_offset(self, query: Select) -> Select:
        return query.limit(self.limit).offset(self.limit * (self.page - 1))


class SearchName(Params):
    name: str | None = Query(
        None,
        max_length=128,
        description="Поиск по частичному вхождению в начале названия ингредиента.",
    )

    async def search(self, query: Select, attr_name: str, model: Sequence[_TM]) -> Select:
        if self.name:
            if model := getattr(model, attr_name, None):
                return query.where(model.like(f"{self.name}%"))

        return query
