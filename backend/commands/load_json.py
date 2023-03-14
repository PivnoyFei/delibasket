# flake8: noqa: F401
"""Загружает данные в таблицу из файла json."""
import asyncio
import json
import os
import sys
from typing import Any

import __init__
import sqlalchemy as sa
from db import Base
from recipes.models import Ingredient, Tag
from settings import DATA_ROOT, DATABASE_URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def async_main(filename: str, model_db: Any) -> None:
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:

        try:
            with open(os.path.join(DATA_ROOT, filename), encoding='utf-8') as file:
                items = dict((item["name"], item) for item in json.load(file)).values()
                for item in items:
                    await session.execute(sa.insert(model_db).values(**item))

        except TypeError:
            print(f'Файл {filename} отсутствует в каталоге data')

        await session.commit()
    await engine.dispose()


command_load = {
    "ingredients.json": Ingredient,
    "tags.json": Tag,
}
data_load = sys.argv
if len(data_load) > 1:
    data: str = data_load[-1]
    if data in command_load:
        asyncio.run(async_main(data, command_load[data]))
    else:
        print(f'Файл {data} отсутствует в каталоге data')
else:
    for i in command_load.keys():
        print('====', i)
        asyncio.run(async_main(i, command_load[i]))
