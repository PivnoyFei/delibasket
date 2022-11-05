import datetime
from typing import Optional
from fastapi.param_functions import Form
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi import status, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request

class GetUser(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str


class UserCreate(GetUser):
    password: str


class UserAuth(OAuth2PasswordRequestForm):
    def __init__(
        self,
        email: EmailStr = Form(),
        password: str  = Form()
    ):
        self.email = email
        self.password = password


class OAuth2PasswordToken(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "token":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Token"},
                )
            else:
                return None
        return param


class UserInDB(BaseModel):
    auth_token: str


class Userfull(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    timestamp: datetime.date
    is_subscribed: Optional[int | bool] = False


class ListUserfull(BaseModel):
    count: int
    results: list[Userfull] = []


class Follow(Userfull):
    recipes: Optional[list] = []
    recipes_count: Optional[int] = 0


class Subscriptions(BaseModel):
    count: int
    results: list[Follow] = []


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None


class TokenPayload(BaseModel):
    sub: EmailStr = None
    exp: int = None