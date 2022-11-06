from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse

from db import database
from users import utils, schemas
from users.models import User

recipe_router = APIRouter(prefix='/api', tags=["users"])
db_user = User(database)


@recipe_router.get("/recipe/")
async def read_users_me(current_user: User = Depends(utils.get_current_user)):
    return current_user
