from db import database
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from users import schemas, utils
from users.models import User
from recipes.models import Tag, Recipe

recipe_router = APIRouter(prefix='/api', tags=["recipe"])
db_user = User(database)
db_Tag = Tag(database)


@recipe_router.get("/tags/")
async def tags(current_user: User = Depends(utils.get_current_user)):
    return current_user



