import os
from datetime import timedelta
from typing import Any

from dotenv import load_dotenv
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, root_validator, validator

load_dotenv()


class Settings(BaseSettings):
    API_V1_STR: str = "/api"

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    POSTGRES_NAME: str | None = "postgres"
    POSTGRES_USER: str | None = "postgres"
    POSTGRES_PASSWORD: str | None = "postgres"
    POSTGRES_SERVER: str | None = "localhost"
    POSTGRES_PORT: int | None = 5432
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    TESTING: bool | None = None

    @root_validator(pre=True)
    def testing_db_connection(cls, value: dict[str, Any]) -> dict:
        if value.get("TESTING", None):
            value["POSTGRES_SERVER"] = "db-test"
        return value

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: str | None, values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )


settings: Settings = Settings()

BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

MEDIA_URL: str = 'media'
MEDIA_ROOT: str = os.path.join(BASE_DIR, MEDIA_URL)
FILES_ROOT: str = os.path.join(MEDIA_ROOT, "files")
DATA_ROOT: str = os.path.join(BASE_DIR, "data")

ALLOWED_TYPES: type[str] = ("jpeg", "jpg", "png", "gif")
INVALID_FILE: str = "Please upload a valid image."
INVALID_TYPE: str = "The type of the image couldn't be determined."

NOT_FOUND: JSONResponse = JSONResponse({"detail": "NotFound"}, status.HTTP_404_NOT_FOUND)

TOKEN_EXP: timedelta = timedelta(weeks=2)
PAGINATION_SIZE: int = 6
