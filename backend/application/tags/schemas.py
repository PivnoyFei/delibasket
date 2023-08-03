from typing import Any

from fastapi import Form
from pydantic import BaseModel

from application.schemas import BaseSchema


class TagCreate(BaseModel):
    name: str = Form(..., description="Название")
    color: str = Form(..., min_length=6, max_length=6, description="Цвет в HEX")
    slug: str = Form(..., description="Уникальный слаг")

    class Config:
        str_strip_whitespace = True
        json_schema_extra = {
            "example": {
                "name": "Завтрак",
                "color": "E26C2D",
                "slug": "breakfast",
            }
        }


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = Form(None, min_length=6, max_length=6)
    slug: str | None = None
    address: str | None = None


class TagOut(BaseSchema):
    name: str
    color: str
    slug: str

    @staticmethod
    async def tuple_to_dict(tags: tuple) -> dict[str, Any]:
        return [
            {"id": pk, "name": name, "color": color, "slug": slug} for pk, name, color, slug in tags
        ]
