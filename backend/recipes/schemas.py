import datetime
from typing import Optional

from fastapi import HTTPException, status
from fastapi.param_functions import Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel, EmailStr
from starlette.requests import Request
