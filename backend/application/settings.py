import os
from typing import Any

from dotenv import load_dotenv
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl, PostgresDsn, validator

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

    TESTING: bool | None = False
    if TESTING:
        POSTGRES_SERVER = "db-test"

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MEDIA_URL = 'media'
MEDIA_ROOT = os.path.join(BASE_DIR, MEDIA_URL)
FILES_ROOT = os.path.join(MEDIA_ROOT, "files")
DATA_ROOT = os.path.join(BASE_DIR, "data")

ALLOWED_TYPES = ("jpeg", "jpg", "png", "gif")
INVALID_FILE = "Please upload a valid image."
INVALID_TYPE = "The type of the image couldn't be determined."

NOT_AUTHENTICATED = JSONResponse({"detail": "Not authenticated"}, status.HTTP_401_UNAUTHORIZED)
NOT_FOUND = JSONResponse({"detail": "NotFound"}, status.HTTP_404_NOT_FOUND)
