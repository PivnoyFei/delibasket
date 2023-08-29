from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.sql.schema import MetaData
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request

from application.auth.permissions import AuthBackend
from application.database import Base, sessionmanager
from application.exceptions import CustomException
from application.routers import router
from application.settings import settings


def init_routers(app_: FastAPI) -> None:
    app_.include_router(router, prefix=settings.API_V1_STR)


def init_listeners(app_: FastAPI) -> None:
    @app_.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.code,
            content={"error_code": exc.error_code, "message": exc.message},
        )


def on_auth_error(request: Request, exc: Exception) -> JSONResponse:
    status_code, error_code, message = 401, None, str(exc)
    if isinstance(exc, CustomException):
        status_code = int(exc.code)
        error_code = exc.error_code
        message = exc.message

    return JSONResponse(
        status_code=status_code,
        content={"error_code": error_code, "message": message},
    )


def make_middleware() -> list[Middleware]:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(
            AuthenticationMiddleware,
            backend=AuthBackend(),
            on_error=on_auth_error,
        ),
    ]
    return middleware


def create_app(init_db: bool | None = True) -> FastAPI:
    lifespan = None
    if init_db:
        sessionmanager.init(settings.SQLALCHEMY_DATABASE_URI)

        @asynccontextmanager
        async def lifespan(app_: FastAPI):
            yield
            if sessionmanager._engine is not None:
                await sessionmanager.close()

    app_ = FastAPI(
        debug=False,
        title="DELIBASKET INGREDIENTS",
        description="Электронная продуктовая корзина",
        version="1.0.1",
        openapi_url=f"{settings.API_V1_STR}/docs/openapi.json",
        redoc_url=f"{settings.API_V1_STR}/docs",
        docs_url="/docs",
        middleware=make_middleware(),
        contact={
            "name": "Смелов Илья",
            "url": "https://github.com/PivnoyFei",
        },
        license_info={
            "name": "BSD 3-Clause",
            "url": "https://github.com/PivnoyFei/delibasket/blob/main/LICENSE",
        },
        lifespan=lifespan,
    )
    init_routers(app_=app_)
    init_listeners(app_=app_)
    return app_


app: FastAPI = create_app()
metadata: MetaData = Base.metadata
