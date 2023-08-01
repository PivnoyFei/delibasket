from fastapi import Form
from pydantic import BaseModel


class IngredientCreate(BaseModel):
    name: str = Form(..., description="Название")
    measurement_unit: str = Form(..., description="Единицы измерения")

    class Config:
        str_strip_whitespace = True
        schema_extra = {
            "example": {
                "name": "Капуста",
                "measurement_unit": "кг",
            }
        }


class IngredientUpdate(BaseModel):
    name: str | None = None
    measurement_unit: str | None = None


class IngredientOut(BaseModel):
    id: int
    name: str
    measurement_unit: str

    class Config:
        from_attributes = True
