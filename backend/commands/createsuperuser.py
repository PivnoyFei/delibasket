# flake8: noqa: F401
""" Создание суперюзера. """

import asyncio
import getpass
from dataclasses import asdict, dataclass

import __init__
import sqlalchemy as sa
from db import Base
from settings import DATABASE_URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from users.models import User
from users.utils import password_context


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


class Createsuperuser:
    def __init__(self, email: str, password: str, username: str, first_name: str, last_name: str) -> None:
        self.user = UserData(email, password, username, first_name, last_name)

    @property
    def get_dataclass(self) -> dict[str]:
        return asdict(self.user)

    def edit(self, key: str, value: str) -> None:
        self.user.__dict__[key] = value

    def check(self, key: str) -> str:
        if key == "password":
            value = getpass.getpass(f"Введите {key}: ")
            if value != getpass.getpass(f"Повторите {key}: "):
                print("Пароли не совпадают")
                return self.check(key)
            value = password_context.hash(value)
        else:
            value = input(f"Введите {key}: ")
            if value == "":
                print(
                    "Пустая строка вы уверены? Если ДА, просто нажмите интер."
                )
                value = input(f"Введите {key}: ")
        return value


async def async_main(a: Createsuperuser) -> None:
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:

        try:
            await session.execute(sa.insert(User).values(a.get_dataclass))

        except TypeError:
            print('email или username уже существует')

        await session.commit()
    await engine.dispose()


a = Createsuperuser("", "", "", "", "")
for key in a.get_dataclass:
    if key not in ("is_active", "is_staff", "is_superuser"):
        a.edit(key, a.check(key))

asyncio.run(async_main(a))
