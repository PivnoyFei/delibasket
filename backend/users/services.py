from db import database
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from users import schemas, utils
from users.models import Follow

user_router = APIRouter(prefix='/api', tags=["users"])
db_follow = Follow(database)


async def users_list(query: list):
    return {"count": len(query), "results": query}
