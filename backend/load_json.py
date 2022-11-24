"""Загружает данные в уже созданую таблицу из файла json."""

import json
import os
import sys

import sqlalchemy

from recipes.models import ingredient, tag
from settings import DATA_ROOT, DATABASE_URL

engine = sqlalchemy.create_engine(DATABASE_URL)
engine.connect()
metadata = sqlalchemy.MetaData(engine)
metadata.reflect(engine)


def load_ingredients(filename):
    try:
        with open(os.path.join(DATA_ROOT, filename), encoding='utf-8') as file:
            f = dict((item["name"], item) for item in json.load(file)).values()

            for item in f:
                engine.execute(ingredient.insert().values(**item))

    except TypeError:
        print(f'Файл {filename} отсутствует в каталоге data')


def load_tags(filename):
    try:
        with open(os.path.join(DATA_ROOT, filename), encoding='utf-8') as file:
            f = dict((item["name"], item) for item in json.load(file)).values()

            for item in f:
                engine.execute(tag.insert().values(**item))

    except FileNotFoundError:
        print(f'Файл {filename} отсутствует в каталоге data')


command_load = {"ingredients.json": load_ingredients, "tags.json": load_tags}
data = sys.argv[-1]
command_load[data](data)
