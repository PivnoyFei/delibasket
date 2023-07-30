# flake8: noqa: F401
"""Загружает данные в таблицу из файла json."""
import asyncio
import json
import os
import sys
from typing import Sequence, TypeVar

import __init__
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from application.ingredients.models import Ingredient
from application.settings import DATA_ROOT, settings
from application.tags.models import Tag

_TM = TypeVar('_TM')


async def async_main(filename: str, model: Sequence[_TM]) -> None:
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        try:
            with open(os.path.join(DATA_ROOT, filename), encoding='utf-8') as file:
                items = dict((item["name"], item) for item in json.load(file)).values()
                for item in items:
                    try:
                        await session.execute(sa.insert(model).values(**item))
                        await session.commit()
                    except:
                        await session.rollback()

        except TypeError:
            print(f'Файл {filename} отсутствует в каталоге data')

    await engine.dispose()
    print("== Успех! ==")


command_load = {"ingredients.json": Ingredient, "tags.json": Tag}
data_load = sys.argv
if len(data_load) > 1:
    data: str = data_load[-1]
    if data in command_load:
        asyncio.run(async_main(data, command_load[data]))
    else:
        print(f'Файл {data} отсутствует в каталоге data')
else:
    for k, v in command_load.items():
        print(f'=== {k} ===')
        asyncio.run(async_main(k, v))
