import datetime
from typing import Optional
from fastapi.param_functions import Form
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi import status, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
