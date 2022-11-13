from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from db import database, engine, metadata
from recipes.api import recipe_router
from settings import MEDIA_ROOT
from users.api import user_router

app = FastAPI()
app.state.database = database
metadata.create_all(engine)


app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")


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


app.include_router(user_router)
app.include_router(recipe_router)
