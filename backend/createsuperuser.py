import getpass
from dataclasses import asdict, dataclass

import sqlalchemy

from settings import DATABASE_URL
from users.models import users
from users.utils import password_context

engine = sqlalchemy.create_engine(DATABASE_URL)
engine.connect()
metadata = sqlalchemy.MetaData(engine)
metadata.reflect(engine)


@dataclass
class User:
    email: str
    password: str
    username: str
    first_name: str
    last_name: str
    is_active: bool = True
    is_staff: bool = True
    is_superuser: bool = True


class Createsuperuser:
    def __init__(self, email, password, username, first_name, last_name):
        self.user = User(email, password, username, first_name, last_name)

    @property
    def get_dataclass(self) -> dict[str]:
        return asdict(self.user)

    def edit(self, key, value) -> None:
        self.user.__dict__[key] = value

    def check(self, key) -> str:
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


a = Createsuperuser("", "", "", "", "")
for key in a.get_dataclass:
    if key not in ("is_active", "is_staff", "is_superuser"):
        a.edit(key, a.check(key))

engine.execute(users.insert().values(a.get_dataclass))
