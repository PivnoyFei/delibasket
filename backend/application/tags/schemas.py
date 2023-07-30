from fastapi import Form
from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str = Form()
    color: str = Form(min_length=6, max_length=6)
    slug: str = Form()


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = Form(None, min_length=6, max_length=6)
    slug: str | None = None
    address: str | None = None


class TagOut(BaseModel):
    id: int
    name: str
    color: str
    slug: str

    class Config:
        orm_mode = True
