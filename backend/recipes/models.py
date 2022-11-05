from databases import Database
from sqlalchemy import Column, ForeignKey, DateTime, Integer, String, Table, UniqueConstraint, Text, CheckConstraint, select
from sqlalchemy.sql import func

from db import metadata
from recipes.schemas import UserCreate, UserInDB, UserAuth

ingredient = Table(
    "ingredient", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(200), unique=True, index=True),
    Column("measurement_unit", String(200)),
    UniqueConstraint('name', 'measurement_unit', name='unique_ingredient')
)
tag = Table(
    "tag", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(200), unique=True, index=True),
    Column("color", String(6), unique=True),
    Column("slug", String(200), unique=True, index=True),
)
recipe = Table(
    "recipe", metadata,
    Column("id", Integer, primary_key=True),
    Column("author_id", Integer, ForeignKey("users.id")),
    Column("name", String(200), unique=True, index=True),
    Column("image", String(200), unique=True),
    Column("text", Text),
    Column("cooking_time", Integer),
    CheckConstraint('cooking_time > 0', name='cooking_time_check'),
    Column("pub_date", DateTime(timezone=True), default=func.now()),
)
recipe_tag = Table(
    "recipe_tag", metadata,
    Column("id", Integer, primary_key=True),
    Column("recipe_id", Integer, ForeignKey("recipe.id")),
    Column("tag_id", Integer, ForeignKey("tag.id")),
)
favorites = Table(
    "favorites", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("recipe_id", Integer, ForeignKey("recipe.id")),
    UniqueConstraint('user', 'recipe', name='unique_for_favorite')
)
cart = Table(
    "cart", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("recipe_id", Integer, ForeignKey("recipe.id")),
    UniqueConstraint('user', 'recipe', name='unique_for_cart')
)
amount_ingredient = Table(
    "amount_ingredient", metadata,
    Column("id", Integer, primary_key=True),
    Column("ingredient_id", Integer, ForeignKey("ingredient.id")),
    Column("recipe_id", Integer, ForeignKey("recipe.id")),
    Column("amount", Integer),
    CheckConstraint('amount > 0', name='amount_check'),
    UniqueConstraint('user', 'recipe', name='unique_for_cart')
)

