from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenBase(BaseModel):
    auth_token: str


class CurrentUser(BaseModel):
    id: int = Field(None, description="Id")
    is_active: bool = Field(False, description="Is active")
    is_staff: bool = Field(False, description="Is staff")
    is_superuser: bool = Field(False, description="Is superuser")

    class Config:
        validate_assignment = True
