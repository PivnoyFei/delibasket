from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, case, func
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.expression import Case, Label
from sqlalchemy.types import NullType


class TimeStampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def list_columns(cls, *args: str) -> list[Any]:
        """
        Получить список всех или некоторых колонок таблицы.
        используйте `join` или `relationship` для сторонних моделей.

        .. code-block:: python

        select(*Your_model.list_columns("your_attr", Your_model.your_attr), Your_other_model.id)
        """
        if args:
            build: list[Any] = []

            for name in args:
                if isinstance(name, str):
                    if attr := getattr(cls, name, None):
                        build.append(attr)
                    else:
                        raise AttributeError(f"класс {cls.__name__} не имеет атрибута {name}")
                elif isinstance(name, (InstrumentedAttribute, Label)):
                    build.append(name)
                else:
                    raise AttributeError(
                        f"`{name}`: допускаются только `str, InstrumentedAttribute`"
                    )

            return build

        return [getattr(cls, c.name) for c in cls.__table__.columns]

    @classmethod
    def json_build_object(cls, *args: str) -> Case[Any]:
        """
        Получить объект в json, со всеми или некоторыми колоноками таблицы.

        .. code-block:: python

        select(Your_model.id, Your_other_model.json_build_object("your_attr"))
        """

        build: list[tuple[str, Any]] = []
        if args:
            for name in args:
                if not isinstance(name, str):
                    raise TypeError(f"атрибут {name} должен быть в формоте `str`")

                if attr := getattr(cls, name, None):
                    build.extend((name, attr))
                else:
                    raise AttributeError(f"класс {cls.__name__} не имеет атрибута {name}")

        else:
            for c in cls.__table__.columns:
                build.extend((c.name, getattr(cls, c.name)))

        return case(
            (
                cls.id != None,
                func.json_build_object(*build),
            ),
            else_=None,
        )

    @classmethod
    def json_agg(cls, *args: str) -> Case[Any]:
        """
        Получить список объектов в json, со всеми или некоторыми колоноками таблицы.

        .. code-block:: python

        select(Your_model.id, Your_other_model.json_agg("your_attr"))
        """
        return case(
            (
                func.count(cls.id) != 0,
                func.json_agg(cls.json_build_object(*args)),
            ),
            else_=None,
        )

    @classmethod
    def array_agg(cls, *args: str) -> Case[Any]:
        """
        Получить список всех или некоторых колонок таблицы.
        используйте `join` или `relationship` для сторонних моделей.

        .. code-block:: python

        select(Your_model.id, Your_model.array_agg("your_attr", Your_model.your_attr)
        """
        return func.array_agg(func.distinct(*cls.list_columns(*args)), type_=NullType)
