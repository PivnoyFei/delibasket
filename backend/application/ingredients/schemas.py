from fastapi import Form
from pydantic import BaseModel


class IngredientCreate(BaseModel):
    name: str = Form()
    measurement_unit: str = Form()


class IngredientUpdate(BaseModel):
    name: str | None = None
    measurement_unit: str | None = None


class IngredientOut(BaseModel):
    id: int
    name: str
    measurement_unit: str

    class Config:
        orm_mode = True
