from typing import Any, Generic, Sequence, TypeVar

from fastapi import Query
from pydantic import AnyUrl, BaseModel, Field
from sqlalchemy import Select, select
from sqlalchemy.sql import func
from starlette.datastructures import URL

from application.recipes.models import Recipe
from application.settings import PAGINATION_SIZE
from application.users.models import User

name_str = "^([А-Яа-я]+|[A-Za-z]+)$"
name_en_str = "^[A-Za-z]+$"

_TS = TypeVar("_TS")
_TM = TypeVar("_TM")


class BaseSchema(BaseModel):
    id: int

    class Config:
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


class SubParams(Params):
    recipes_limit: int = Query(
        3,
        ge=1,
        le=1000,
        description="Количество объектов внутри поля recipes.",
    )

    async def to_dict(self, results: list) -> list:
        return [
            {
                "id": items.id,
                "email": items.email,
                "username": items.username,
                "first_name": items.first_name,
                "last_name": items.last_name,
                "is_subscribed": items.is_subscribed,
                "recipes": items.recipes,
                "recipes_count": self.recipes_limit,
            }
            for items in results
        ]


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


class SearchUser(Params):
    first_name: str | None = Query(
        None, regex=name_str, max_length=256, description="Поиск по имени"
    )
    last_name: str | None = Query(
        None, regex=name_str, max_length=256, description="Поиск по фамилии"
    )

    async def search(self, query: Select) -> Select:
        for attr_name in ("last_name", "first_name"):
            if search := getattr(self, attr_name, None):
                query = query.where(getattr(User, attr_name).like(f"{search}%"))

        return query


class IsFavoritedCartRecipeMixin(BaseModel):
    is_favorited: bool = Query(
        False, description="Показывать только рецепты, находящиеся в списке избранного."
    )
    is_in_shopping_cart: bool = Query(
        False, description="Показывать только рецепты, находящиеся в списке покупок."
    )


class SearchRecipe(Params, IsFavoritedCartRecipeMixin):
    author: int = Query(0, description="Показывать рецепты только автора с указанным id.")
    tags: list[str] = Field(
        Query([], description="Показывать рецепты только с указанными тегами (по slug)")
    )

    async def search(self, query: Select) -> tuple[Select, Select] | list[Select]:
        count = await self.count(Recipe)
        query = await self.limit_offset(query)

        if self.author:
            return [i.where(Recipe.author_id == self.author) for i in (count, query)]
        return count, query


class Result(BaseModel, Generic[_TS]):
    count: int = Field(0, description="Общее количество объектов в базе.")
    next: AnyUrl | None = Field(None, description="Ссылка на следующую страницу.")
    previous: AnyUrl | None = Field(None, description="Ссылка на предыдущую страницу.")
    results: list[_TS] = Field([], description="Список объектов текущей страницы.")

    @staticmethod
    async def result(url: URL, count: int, params: Params, results: list) -> dict[str, Any]:
        """Составляет json ответ для пользователя в соответствии с требованиями.
        Составляет следующую, предыдущую и количество страниц для пагинации."""
        page = params.page
        return {
            "count": count,
            "next": (
                str(url.replace_query_params(page=page + 1)) if params.has_next(count) else None
            ),
            "previous": (
                str(url.replace_query_params(page=page - 1)) if params.has_previous else None
            ),
            "results": results,
        }
