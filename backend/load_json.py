import json
import os

import sqlalchemy

from recipes.models import ingredient, tag
from settings import DATA_ROOT, DATABASE_URL

engine = sqlalchemy.create_engine(DATABASE_URL)
engine.connect()
metadata = sqlalchemy.MetaData(engine)
metadata.reflect(engine)

"""Загружает данные в уже созданую таблицу из файла json."""
try:
    filename = "ingredients.json"
    with open(os.path.join(DATA_ROOT, filename), encoding='utf-8') as file:
        file = dict((item["name"], item) for item in json.load(file)).values()

        for item in file:
            engine.execute(ingredient.insert().values(**item))

except TypeError:
    print(f'Файл {filename} отсутствует в каталоге data')

try:
    filename = "tags.json"
    with open(os.path.join(DATA_ROOT, filename), encoding='utf-8') as file:
        file = dict((item["name"], item) for item in json.load(file)).values()

        for item in file:
            engine.execute(tag.insert().values(**item))

except FileNotFoundError:
    print(f'Файл {filename} отсутствует в каталоге data')
