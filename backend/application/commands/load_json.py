# flake8: noqa: F401
"""Загружает данные в таблицу из файла json."""
import asyncio
import json
import os

import __init__

from application.database import sessionmanager
from application.managers import Manager
from application.settings import DATA_ROOT, settings
from application.tags.models import Tag


async def async_main() -> None:
    try:
        sessionmanager.init(settings.SQLALCHEMY_DATABASE_URI, "tags")
        with open(os.path.join(DATA_ROOT, "tags.json"), encoding="utf-8") as file:
            items = dict((item["name"], item) for item in json.load(file)).values()
            for item in items:
                await Manager(Tag, "tags").create(item)

        print("== Успех! ==")

    except TypeError:
        print("Файл <tags.json> отсутствует в каталоге data")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await sessionmanager.close("tags")


asyncio.run(async_main())
