import logging
import os
from datetime import timedelta
from typing import Any

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="=== %(levelname)s - %(pathname)s - %(funcName)s: %(lineno)d - %(message)s",
    datefmt="%H:%M:%S",
)


class Settings(BaseSettings):
    API_V1_STR: str = "/api"

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    POSTGRES_NAME: str | None = "postgres"
    POSTGRES_USER: str | None = "postgres"
    POSTGRES_PASSWORD: str | None = "postgres"
    POSTGRES_SERVER: str | None = "delibasket-db"
    POSTGRES_PORT: int | None = 5432

    REDIS_HOST: str | None = "delibasket-redis"
    REDIS_PORT: int | None = 6379
    REDIS_PASSWORD: str | None = "qwerty"

    BACKEND_TOKEN_EXP: int | None = 10

    TESTING: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def testing_db_connection(cls, data: dict[str, Any]) -> dict:
        if data.get("TESTING", None):
            data["POSTGRES_SERVER"] = "db-test"
        return data

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_NAME or ''}"
        )

    @property
    def REDIS_URL(self) -> RedisDsn:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def TOKEN_EXP(self) -> timedelta:
        return timedelta(seconds=self.BACKEND_TOKEN_EXP)


settings: Settings = Settings()

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

MEDIA_URL: str = "media"
MEDIA_ROOT: str = os.path.join(BASE_DIR, MEDIA_URL)
FILES_ROOT: str = os.path.join(MEDIA_ROOT, "files")
DATA_ROOT: str = os.path.join(BASE_DIR, "data")

ALLOWED_TYPES: tuple[str, str, str, str] = ("jpeg", "jpg", "png", "gif")
INVALID_FILE: str = "Please upload a valid image."
INVALID_TYPE: str = "The type of the image couldn't be determined."

PAGINATION_SIZE: int = 6
