from typing import Generic, Sequence, TypeVar

from fastapi import Query
from pydantic import AnyUrl, BaseModel, Field
from pydantic.dataclasses import dataclass
from pydantic.generics import GenericModel
from sqlalchemy import Select, select
from sqlalchemy.sql import func

from application.recipes.models import Recipe
from application.settings import PAGINATION_SIZE
from application.users.models import User

name_str = "^([А-Яа-я]+|[A-Za-z]+)$"
name_en_str = "^[A-Za-z]+$"

_TS = TypeVar('_TS')
_TM = TypeVar('_TM')


@dataclass
class QueryParams:
    tags: list[int | str] = Query(
        None,
        description="Показывать рецепты только с указанными тегами (по slug)",
    )


class BaseSchema(BaseModel):
    id: int

    class Config:
        orm_mode = True


class Params(BaseModel):
    page: int = Query(1, ge=1, description="Номер страницы.")
    limit: int = Query(
        PAGINATION_SIZE,
        ge=1,
        le=1000,
        description="Количество объектов на странице.",
    )

    async def search(self) -> Select:
        raise NotImplementedError("Метод должен быть переопределен.")

    @staticmethod
    async def count(model: Sequence[_TM]) -> Select:
        return select(func.count(model.id).label("is_count"))

    async def limit_offset(self, query: Select) -> Select:
        return query.limit(self.limit).offset(self.limit * (self.page - 1))


class SubscriptionsParams(Params):
    recipes_limit: int = Query(
        3,
        ge=1,
        le=1000,
        description="Количество объектов внутри поля recipes.",
    )

    async def limit_offset(self, query: Select) -> Select:
        return query.limit(self.recipes_limit)

    async def to_dict(self, results: list) -> list:
        return [
            {
                "id": items.id,
                "email": items.email,
                "username": items.username,
                "first_name": items.first_name,
                "last_name": items.last_name,
                "is_subscribed": items.is_subscribed,
            }
            for items in results
        ]


class SearchName(Params):
    name: str = Query(
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
    first_name: str = Query(None, regex=name_str, max_length=256, description="Поиск по имени")
    last_name: str = Query(None, regex=name_str, max_length=256, description="Поиск по фамилии")

    async def search(self, query: Select) -> Select:
        for attr_name in ("last_name", "first_name"):
            if search := getattr(self, attr_name, None):
                query = query.where(getattr(User, attr_name).like(f"{search}%"))

        return query


class IsFavoritedCartRecipeMixin(BaseModel):
    is_favorited: int = Query(
        None, description="Показывать только рецепты, находящиеся в списке избранного."
    )
    is_in_shopping_cart: int = Query(
        None, description="Показывать только рецепты, находящиеся в списке покупок."
    )


class SearchRecipe(Params, IsFavoritedCartRecipeMixin):
    author: int = Query(None, description="Показывать рецепты только автора с указанным id.")

    async def search(self, query: Select) -> tuple[Select, Select] | list[Select]:
        count = await self.count(Recipe)
        query = await self.limit_offset(query)

        if self.author:
            return [i.where(Recipe.author_id == self.author) for i in (count, query)]
        return count, query


class Result(GenericModel, Generic[_TS]):
    count: int = Field(0, description="Общее количество объектов в базе.")
    next: AnyUrl = Field(None, description="Ссылка на следующую страницу.")
    previous: AnyUrl = Field(None, description="Ссылка на предыдущую страницу.")
    results: list[_TS] | None = Field([], description="Список объектов текущей страницы.")
