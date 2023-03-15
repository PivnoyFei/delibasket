from typing import Any

from db import Base, engine
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from recipes import api_recipe
from settings import MEDIA_ROOT
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from users import api_auth, api_user

app = FastAPI(title="DELIBASKET")
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: Any) -> JSONResponse:
    return JSONResponse({"detail": f"{exc.detail}"}, exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: Any) -> JSONResponse:
    message = ""
    for pydantic_error in exc.errors():
        loc, msg = pydantic_error["loc"], pydantic_error["msg"]
        filtered_loc = loc[1:] if loc[0] in ("body", "query", "path") else loc
        field_string = ".".join(filtered_loc)
        message += f"\n{field_string} - {msg}"
    return JSONResponse(
        {"detail": "Invalid request", "errors": message},
        status.HTTP_422_UNPROCESSABLE_ENTITY
    )


app.include_router(api_recipe.router)
app.include_router(api_user.router, prefix="/api")
app.include_router(api_auth.router, prefix="/api")
