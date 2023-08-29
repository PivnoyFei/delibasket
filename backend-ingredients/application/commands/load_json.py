# flake8: noqa: F401
"""Загружает данные в таблицу из файла json."""
import asyncio
import json
import os

import __init__

from application.database import sessionmanager
from application.ingredients.models import Ingredient
from application.managers import Manager
from application.settings import DATA_ROOT, settings


async def async_main() -> None:
    try:
        sessionmanager.init(settings.SQLALCHEMY_DATABASE_URI, "ingredients")
        with open(os.path.join(DATA_ROOT, "ingredients.json"), encoding="utf-8") as file:
            items = dict((item["name"], item) for item in json.load(file)).values()
            for item in items:
                await Manager(Ingredient, "ingredients").create(item)

        print("== Успех! ==")

    except TypeError:
        print("Файл <ingredients.json> отсутствует в каталоге data")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await sessionmanager.close("ingredients")


asyncio.run(async_main())
