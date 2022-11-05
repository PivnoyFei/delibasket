from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from db import database, engine, metadata
from settings import STATIC_ROOT # , TEMPLATES_DIR
from users.api import user_router

app = FastAPI()
app.state.database = database
metadata.create_all(engine)

#templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


@app.on_event("startup")
async def startup() -> None:
    database_ = app.state.database
    if not database_.is_connected:
        await database_.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    database_ = app.state.database
    if database_.is_connected:
        await database_.disconnect()


#@app.exception_handler(StarletteHTTPException)
#async def custom_exception_handler(request, exc):
#    return templates.TemplateResponse("error.html", {
#        "request": request,
#        "status": exc.status_code,
#        "detail": exc.detail})


app.include_router(user_router)
