from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, UniqueConstraint

from application.database import Base
from application.models import TimeStampMixin


class Ingredient(Base, TimeStampMixin):
    __table_args__ = (UniqueConstraint('name', 'measurement_unit'),)

    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, index=True)
    measurement_unit = Column(String(200))


class AmountIngredient(Base, TimeStampMixin):
    __table_args__ = (
        UniqueConstraint('ingredient_id', 'recipe_id'),
        CheckConstraint('amount > 0'),
    )

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipe.id", ondelete='CASCADE'))
    ingredient_id = Column(Integer, ForeignKey("ingredient.id", ondelete='CASCADE'))
    amount = Column(Integer)
