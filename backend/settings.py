import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import status
from fastapi.responses import JSONResponse

env_path = Path(".") / "infra/.env"
load_dotenv(dotenv_path=env_path)


POSTGRES_DB = os.getenv("POSTGRES_DB", default="postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", default="postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", default="postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", default="localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", default="5432")

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', default='localhost')

TESTING = os.getenv("TESTING", default=False)
if TESTING:
    POSTGRES_SERVER = "db-test"
DATABASE_URL = (f"postgresql://{POSTGRES_USER}:"
                f"{POSTGRES_PASSWORD}@"
                f"{POSTGRES_SERVER}:"
                f"{POSTGRES_PORT}/"
                f"{POSTGRES_DB}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, MEDIA_URL)
FILES_ROOT = os.path.join(MEDIA_ROOT, "files")
DATA_ROOT = os.path.join(BASE_DIR, "data")

ALLOWED_TYPES = ("jpeg", "jpg", "png", "gif")
INVALID_FILE = "Please upload a valid image."
INVALID_TYPE = "The type of the image couldn't be determined."

NOT_AUTHENTICATED = JSONResponse(
    {"detail": "Not authenticated"}, status.HTTP_401_UNAUTHORIZED)
NOT_FOUND = JSONResponse({"detail": "NotFound"}, status.HTTP_404_NOT_FOUND)
