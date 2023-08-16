# flake8: noqa: F401
""" Создание суперюзера. """

import asyncio
import getpass
from typing import Any

import __init__
import bcrypt
from pydantic import BaseModel, EmailStr, Field, ValidationError, constr
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from application.schemas import name_en_str, name_str
from application.settings import settings
from application.users.models import User

# user = Manager(User)


class EmailField(BaseModel):
    email: EmailStr


class NameField(BaseModel):
    name: constr(pattern=name_str, max_length=128) = Field(min_length=1)


class NameEnField(BaseModel):
    username: constr(pattern=name_en_str, max_length=128) = Field(min_length=1)


class Createsuperuser:
    items = {
        "email": None,
        "password": None,
        "username": None,
        "first_name": None,
        "last_name": None,
        "is_active": True,
        "is_staff": True,
        "is_superuser": True,
    }

    def __setitem__(self, key: str, value: str) -> None:
        self.items[key] = value

    def check(self, key: str) -> str:
        if key == "password":
            value = getpass.getpass(f"Введите {key}: ").strip()
            if value != getpass.getpass(f"Повторите {key}: ").strip():
                print("Пароли не совпадают")
                return self.check(key)
            value = bcrypt.hashpw(bytes(value, "utf-8"), bcrypt.gensalt())

        else:
            value = input(f"Введите {key}: ").strip()
            if key == "email":
                try:
                    EmailField(**{"email": value})
                except (ValidationError, TypeError):
                    print("Некорректный Email")
                    return self.check(key)

            elif key == "username":
                try:
                    NameEnField(**{"username": value})
                except (ValidationError, TypeError):
                    print("Username должен содержать только английские буквы")
                    return self.check(key)

            elif key in ("first_name", "last_name"):
                try:
                    NameField(**{"name": value})
                except (ValidationError, TypeError):
                    print("Имя и фамилия могут состоять только из русских и английских букв")
                    return self.check(key)

        return value


async def async_main(a: Createsuperuser) -> None:
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        try:
            await session.execute(insert(User).values(**a.items))
            await session.commit()
            print("== Пользователь сохранен! ==")

        except TypeError as e:
            await session.rollback()
            print(f"email или username уже существует {e}")

    await engine.dispose()


s = Createsuperuser()
for key in ("email", "username", "first_name", "last_name", "password"):
    s[key] = s.check(key)

asyncio.run(async_main(s))
