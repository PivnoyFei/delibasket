import logging
import os
from datetime import timedelta

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="==logging== %(levelname)s - %(pathname)s - %(funcName)s: %(lineno)d - %(message)s",
    datefmt="%H:%M:%S",
)


class RedisSettings(BaseSettings):
    REDIS_HOST: str | None = "delibasket-redis"
    REDIS_PORT: int | None = 6379
    REDIS_PASSWORD: str | None = "qwerty"

    @property
    def REDIS_URL(self) -> RedisDsn:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"


class PostgresSettings(BaseSettings):
    SCHEMA_NAME: str | None = "main"

    POSTGRES_NAME: str | None = "postgres"
    POSTGRES_USER: str | None = "postgres"
    POSTGRES_PASSWORD: str | None = "postgres"
    POSTGRES_SERVER: str | None = "delibasket-db"
    POSTGRES_PORT: int | None = 5432

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_NAME or ''}"
        )


class Settings(RedisSettings, PostgresSettings):
    API_V1_STR: str = "/api"
    BACKEND_TOKEN_EXP: int | None = 10
    TESTING: bool | None = False

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []
    INGREDIENTS_DOMAIN: str | None = "host.docker.internal:9989"

    @property
    def TOKEN_EXP(self) -> timedelta:
        return timedelta(seconds=self.BACKEND_TOKEN_EXP)

    @property
    def INGREDIENTS_URL(self) -> str:
        return f"http://{self.INGREDIENTS_DOMAIN}{self.API_V1_STR}/ingredients/recipe/"


class SettingsTest(Settings):
    POSTGRES_NAME_TEST: str | None = "postgres"
    POSTGRES_USER_TEST: str | None = "postgres"
    POSTGRES_PASSWORD_TEST: str | None = "postgres"
    POSTGRES_SERVER_TEST: str | None = "db-test"
    POSTGRES_PORT_TEST: int | None = 6000

    @property
    def SQLALCHEMY_DATABASE_URI_TEST(self) -> PostgresDsn:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER_TEST}:"
            f"{self.POSTGRES_PASSWORD_TEST}@"
            f"{self.POSTGRES_SERVER_TEST}:"
            f"{self.POSTGRES_PORT_TEST}/"
            f"{self.POSTGRES_NAME_TEST or ''}"
        )


settings: Settings = Settings()
settings_test: SettingsTest = SettingsTest()

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

MEDIA_URL: str = "media"
MEDIA_ROOT: str = os.path.join(BASE_DIR, MEDIA_URL)
FILES_ROOT: str = os.path.join(MEDIA_ROOT, "files")
DATA_ROOT: str = os.path.join(BASE_DIR, "data")

ALLOWED_TYPES: tuple[str, str, str, str] = ("jpeg", "jpg", "png", "gif")
INVALID_FILE: str = "Please upload a valid image."
INVALID_TYPE: str = "The type of the image couldn't be determined."

PAGINATION_SIZE: int = 6
