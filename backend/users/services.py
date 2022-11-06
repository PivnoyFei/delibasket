from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse

from db import database
from users import utils
from users.models import Follow
from users.schemas import GetUser, UserToken, UserCreate, UserAuth, Userfull

user_router = APIRouter(prefix='/api', tags=["users"])
db_follow = Follow(database)


async def users_list(query: list):
    return {"count": len(query), "results": query}
