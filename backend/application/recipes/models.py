from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import and_, case, func
from sqlalchemy.sql.functions import concat
from starlette.requests import Request

from application.database import Base
from application.models import TimeStampMixin
from application.settings import MEDIA_URL
from application.users.models import User


class Favorite(Base, TimeStampMixin):
    __table_args__ = (UniqueConstraint('user_id', 'recipe_id'),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE'))
    recipe_id = Column(Integer, ForeignKey("recipe.id", ondelete='CASCADE'))

    @classmethod
    def is_favorited(cls, user_id: int | None = None):
        return case(
            (and_(user_id != None, cls.user_id == user_id), "True"),
            else_="False",
        ).label("is_favorited")


class Cart(Base, TimeStampMixin):
    __table_args__ = (UniqueConstraint('user_id', 'recipe_id'),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE'))
    recipe_id = Column(Integer, ForeignKey("recipe.id", ondelete='CASCADE'))

    @classmethod
    def is_in_shopping_cart(cls, user_id: int | None = None):
        return case(
            (and_(user_id != None, cls.user_id == user_id), "True"),
            else_="False",
        ).label("is_in_shopping_cart")


class Recipe(Base, TimeStampMixin):
    __table_args__ = (CheckConstraint('cooking_time > 0'),)

    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, index=True)
    image = Column(String(200), unique=True)
    text = Column(Text)
    cooking_time = Column(Integer)
    pub_date = Column(DateTime(timezone=True), default=func.now())

    author_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE'))
    author = relationship(User)

    tags = relationship("Tag", secondary="recipe_tag")
    favorites = relationship(Favorite)
    carts = relationship(Cart)

    @classmethod
    def image_path(cls, request: Request):
        return concat(f"{request.base_url}{MEDIA_URL}/", cls.image).label("image")
