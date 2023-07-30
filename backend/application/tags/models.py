from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint

from application.database import Base
from application.models import TimeStampMixin

recipe_tag = Table(
    "recipe_tag",
    Base.metadata,
    Column("recipe_id", Integer, ForeignKey("recipe.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tag.id", ondelete="CASCADE")),
    UniqueConstraint('recipe_id', 'tag_id', name='unique_for_recipe_tag'),
)


class Tag(Base, TimeStampMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, index=True)
    color = Column(String(6), unique=True)
    slug = Column(String(200), unique=True, index=True)
