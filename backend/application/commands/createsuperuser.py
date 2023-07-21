# flake8: noqa: F401
""" Создание суперюзера. """

import asyncio
import getpass
from dataclasses import asdict, dataclass

import __init__
import bcrypt
import sqlalchemy as sa
from pydantic import BaseModel, EmailStr, Field, ValidationError, constr
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from application.database import scoped_session
from application.schemas import name_en_str, name_str
from application.settings import settings
from application.users.models import User


@dataclass
class UserData:
    email: str
    password: str
    username: str
    first_name: str
    last_name: str
    is_active: bool = True
    is_staff: bool = True
    is_superuser: bool = True


class EmailField(BaseModel):
    email: EmailStr


class NameField(BaseModel):
    name: constr(regex=name_str, max_length=128) = Field(min_length=1)


class NameEnField(BaseModel):
    username: constr(regex=name_en_str, max_length=128) = Field(min_length=1)


class Createsuperuser:
    def __init__(
        self, email: str, password: str, username: str, first_name: str, last_name: str
    ) -> None:
        self.user = UserData(email, password, username, first_name, last_name)

    @property
    def get_dataclass(self) -> dict[str]:
        return asdict(self.user)

    def edit(self, key: str, value: str) -> None:
        self.user.__dict__[key] = value

    def check(self, key: str, required: str | None = '') -> str:
        if key not in ("first_name", "last_name"):
            required = '*'

        if key == "password":
            value = getpass.getpass(f"Введите {key}{required}: ").strip()
            if value != getpass.getpass(f"Повторите {key}{required}: ").strip():
                print("Пароли не совпадают")
                return self.check(key)
            value = bcrypt.hashpw(bytes(value, "utf-8"), bcrypt.gensalt())

        else:
            value = input(f"Введите {key}{required}: ").strip()
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
                    if value:
                        NameField(**{"name": value})
                except (ValidationError, TypeError):
                    print("Имя и фамилия могут состоять только из русских и английских букв")
                    return self.check(key)

        return value


async def async_main(a: Createsuperuser) -> None:
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    # async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with scoped_session() as session:
        try:
            await session.execute(sa.insert(User).values(a.get_dataclass))
            await session.commit()

        except TypeError:
            print('email или username уже существует')

    await engine.dispose()
    print("== Пользователь сохранен! ==")


a = Createsuperuser("", "", "", "", "")
for key in ("email", "username", "first_name", "last_name", "password"):
    a.edit(key, a.check(key))

asyncio.run(async_main(a))
