import datetime
from typing import Optional, Dict, Any
from fastapi.param_functions import Form
from pydantic import BaseModel, EmailStr, Field
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi import status, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
from fastapi.security.base import SecurityBase

class GetUser(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str


class UserCreate(GetUser):
    password: str


class UserAuth(OAuth2PasswordRequestForm):
    #email: EmailStr = Field(..., description="user email"),
    #password: str  = Field(..., min_length=5, max_length=24, description="user password")

    def __init__(
        self,
        grant_type: str = Form(default=None, regex="password"),
        email: EmailStr = Form(),
        password: str = Form(),
        scope: str = Form(default=""),
        client_id: Optional[str] = Form(default=None),
        client_secret: Optional[str] = Form(default=None),
    ):
        self.grant_type = grant_type
        self.email = email
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


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


class UserToken(BaseModel):
    auth_token: str


class Userfull(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_subscribed: Optional[str | bool] = False


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
    sub: int = None
    exp: int = None