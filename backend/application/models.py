from datetime import datetime

from sqlalchemy import Column, DateTime, case, func


class TimeStampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def list_columns(cls, *args: str | None) -> list:
        """
        Получить список всех или некоторых колонок таблицы.

        .. code-block:: python

        select(*Your_model.list_columns("your_attr"), Your_other_model.id)
        """
        if args:
            for name in args:
                if not hasattr(cls, name):
                    raise AttributeError(f"класс {cls.__name__} не имеет атрибута {name}")

            return [getattr(cls, name) for name in args]

        return [getattr(cls, c.name) for c in cls.__table__.columns]

    @classmethod
    def json_build_object(cls, *args: str | None):
        """
        Получить объект в json, со всеми или некоторыми колоноками таблицы.

        .. code-block:: python

        select(Your_model.id, Your_other_model.json_build_object("your_attr"))
        """

        build = []
        if args:
            for name in args:
                if attr := getattr(cls, name, None):
                    build.extend((name, attr))
                else:
                    raise AttributeError(f"класс {cls.__name__} не имеет атрибута {name}")

        else:
            for c in cls.__table__.columns:
                build.extend((c.name, getattr(cls, c.name)))

        return case(
            (cls.id != None, func.json_build_object(*build)),
            else_=None,
        ).label(cls.__tablename__)

    @classmethod
    def json_agg(cls, *args: str | None):
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
        ).label(cls.__tablename__)
