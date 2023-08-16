from datetime import datetime
from typing import Generic, Sequence, TypeVar

from asyncpg.exceptions import UniqueViolationError
from sqlalchemy import delete, insert, select, update

from application.database import scoped_session
from application.schemas import Params

_TM = TypeVar("_TM")
_TS = TypeVar("_TS", bound=Params)


class BaseManager(Generic[_TM]):
    def __init__(self, model: _TM):
        self.model = model


class Manager(BaseManager):
    """
    Общий менеджер моделей, позволяет создать любую модель.
    Получить список моделей или одну по id со всеми значениями.
    Получить список с фильтром по str полю.
    Удалить любую модель и сделать обновление модели.

    .. code-block:: python
        your_variable = Managers(YourModel)

        async def your("/your/"):
            await your_variable.create(your_items)
    """

    async def is_id(self, pk: int) -> _TM | None:
        async with scoped_session() as session:
            query = await session.execute(select(self.model.id).where(self.model.id == pk))
            return query.one_or_none()

    async def create(self, items: dict) -> _TM | None:
        try:
            async with scoped_session() as session:
                query = await session.execute(
                    insert(self.model).values(**items).returning(self.model)
                )
                await session.commit()
                return query.scalar()
        except UniqueViolationError as e:
            print(f"== Manager == create == {e}")
            return None

    async def by_id(self, pk: int) -> _TM | None:
        async with scoped_session() as session:
            return await session.scalar(select(self.model).where(self.model.id == pk))

    async def get_all(
        self,
        params: Sequence[_TS],
        attr_name: str,
        query_in: list | None = None,
    ) -> tuple[int, list[_TM]]:
        async with scoped_session() as session:
            count = await params.count(self.model)
            query = await params.limit_offset(select(*query_in))
            count, query = [await params.search(i, attr_name, self.model) for i in (count, query)]
            return await session.scalar(count), list(await session.scalars(query))

    async def get_all_list(
        self,
        params: Sequence[_TS],
        attr_name: str,
        query_in: list | None = None,
    ) -> list:
        async with scoped_session() as session:
            query = await params.search(select(*query_in), attr_name, self.model)
            query = await session.execute(await params.limit_offset(query))
            return query.all()

    async def update(self, items: dict, pk: int) -> _TM | None:
        async with scoped_session() as session:
            try:
                query = await session.execute(
                    update(self.model)
                    .values(**items, updated_at=datetime.utcnow())
                    .where(self.model.id == pk)
                    .returning(self.model)
                )
                await session.commit()
                return query.scalar()

            except Exception as e:
                await session.rollback()
                print(f"== Manager == update == {e}")
                return None

    async def delete(self, pk: int) -> bool:
        async with scoped_session() as session:
            try:
                await session.execute(delete(self.model).where(self.model.id == pk))
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                print(f"== Manager == delete == {e}")
                return False
