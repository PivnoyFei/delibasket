"""Загружает данные в уже созданую таблицу из файла json."""

import json
import os
import sys

import sqlalchemy

from recipes.models import ingredient, tag
from settings import DATA_ROOT, DATABASE_URL


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


engine = sqlalchemy.create_engine(DATABASE_URL)
engine.connect()
metadata = sqlalchemy.MetaData(engine)
metadata.reflect(engine)

command_load = {"ingredients.json": load_ingredients, "tags.json": load_tags}
data = sys.argv
if len(data) > 1:
    data = data[-1]
    if data in command_load:
        command_load[data](data)
    else:
        print(f'Файл {data} отсутствует в каталоге data')
else:
    for i in command_load.keys():
        command_load[i](i)
