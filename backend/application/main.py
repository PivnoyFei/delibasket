from os.path import isdir
from typing import Any

from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from application.database import Base, engine
from application.exceptions import CustomException
from application.routers import router
from application.settings import MEDIA_ROOT, settings


def init_routers(app_: FastAPI) -> None:
    app_.include_router(router, prefix=settings.API_V1_STR)


def init_listeners(app_: FastAPI) -> None:
    @app_.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.code,
            content={"error_code": exc.error_code, "message": exc.message},
        )


def make_middleware() -> list[Middleware]:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],  # settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]
    return middleware


def create_app() -> FastAPI:
    app_ = FastAPI(
        title="DELIBASKET",
        description=None,
        version="1.0.1",
        openapi_url=f"{settings.API_V1_STR}/docs/openapi.json",
        redoc_url=f"{settings.API_V1_STR}/docs",
        middleware=make_middleware(),
    )
    init_routers(app_=app_)
    init_listeners(app_=app_)
    return app_


app = create_app()
if MEDIA_ROOT and isdir(MEDIA_ROOT):
    app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")

metadata = Base.metadata
