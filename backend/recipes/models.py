from asyncpg.exceptions import UniqueViolationError
from sqlalchemy import (CheckConstraint, Column, DateTime, ForeignKey, Integer,
                        String, Table, Text, UniqueConstraint, case, select)
from sqlalchemy.sql import func

from db import Base, metadata
from users.models import User

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
    Column("author_id", Integer, ForeignKey("users.id", ondelete='CASCADE')),
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
    Column("recipe_id", Integer, ForeignKey("recipe.id", ondelete='CASCADE')),
    Column("tag_id", Integer, ForeignKey("tag.id", ondelete='CASCADE')),
)
favorites = Table(
    "favorites", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete='CASCADE')),
    Column("recipe_id", Integer, ForeignKey("recipe.id", ondelete='CASCADE')),
    UniqueConstraint('user_id', 'recipe_id', name='unique_for_favorite')
)
cart = Table(
    "cart", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete='CASCADE')),
    Column("recipe_id", Integer, ForeignKey("recipe.id", ondelete='CASCADE')),
    UniqueConstraint('user_id', 'recipe_id', name='unique_for_cart')
)
amount_ingredient = Table(
    "amount_ingredient", metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "ingredient_id",
        Integer,
        ForeignKey("ingredient.id", ondelete='CASCADE')
    ),
    Column("recipe_id", Integer, ForeignKey("recipe.id", ondelete='CASCADE')),
    Column("amount", Integer),
    CheckConstraint('amount > 0', name='amount_check'),
    UniqueConstraint(
        'ingredient_id', 'recipe_id', name='unique_for_amount_ingredient')
)


class Tag(Base):
    async def create_tag(self, tag_items):
        try:
            query = (
                tag.insert().values(
                    name=tag_items.name,
                    color=tag_items.color,
                    slug=tag_items.slug,
                )
            )
            return await self.database.execute(query)
        except UniqueViolationError as e:
            return e

    async def get_tags(self, pk: int = None) -> list | None:
        query = select([tag])
        if pk:
            query = query.where(tag.c.id == pk)
            return await self.database.fetch_one(query)
        return await self.database.fetch_all(query)

    async def get_tags_by_recipe_id(self, pk: int):
        tags_dict = (
            select([tag])
            .join(recipe_tag, recipe_tag.c.tag_id == tag.c.id)
            .where(recipe_tag.c.recipe_id == pk)
        )
        return await self.database.fetch_all(tags_dict)


class Ingredient(Base):
    async def create_ingredient(self, ingredient_items) -> int:
        try:
            query = (
                ingredient.insert().values(
                    name=ingredient_items.name,
                    measurement_unit=ingredient_items.measurement_unit,
                )
            )
            return await self.database.execute(query)
        except UniqueViolationError as e:
            return e

    async def get_ingredient(self, pk: int = None) -> list | None:
        query = select([ingredient])
        if pk:
            query = query.where(ingredient.c.id == pk)
            return await self.database.fetch_one(query)
        return await self.database.fetch_all(query)


class Amount(Base):
    async def get_amount_by_recipe_id(self, pk: int):
        amount_dict = (
            select([ingredient, amount_ingredient.c.amount])
            .join(
                ingredient,
                amount_ingredient.c.ingredient_id == ingredient.c.id
            )
            .where(amount_ingredient.c.recipe_id == pk)
        )
        return await self.database.fetch_all(amount_dict)


class Recipe(Base):
    async def create_recipe(
        self, recipe_item, ingredients, tags
    ):

        try:
            recipe_id = await self.database.execute(
                recipe.insert().values(**recipe_item)
            )
            tags = [{"recipe_id": recipe_id, "tag_id": i} for i in tags]
            await self.database.execute(recipe_tag.insert().values(tags))

            ingredients = [
                {
                    "recipe_id": recipe_id,
                    "ingredient_id": i.ingredient_id,
                    "amount": i.amount
                }
                for i in ingredients
            ]
            await self.database.execute(
                amount_ingredient.insert().values(ingredients)
            )
            return recipe_id

        except UniqueViolationError as e:
            return e

    async def get_recipe_by_author(self, pk: int):
        return await self.database.fetch_all(
            select(
                recipe.c.id,
                recipe.c.name,
                recipe.c.image,
                recipe.c.cooking_time,
            )
            .where(recipe.c.author_id == pk)
        )

    async def get_recipe_by_id(self, pk: int, auth: int = None):
        query = (
            select(
                recipe.c.id,
                recipe.c.name,
                recipe.c.image,
                recipe.c.id.label("tags"),
                recipe.c.author_id.label("author"),
                recipe.c.id.label("ingredients"),
                recipe.c.text,
                recipe.c.cooking_time,
                case([(favorites.c.user_id == recipe.c.author_id, "True")],
                     else_="False").label("is_favorited"),
                case([(cart.c.user_id == recipe.c.author_id, "True")],
                     else_="False").label("is_in_shopping_cart")
            )
            .join(favorites, favorites.c.recipe_id == recipe.c.id, full=True)
            .join(cart, cart.c.recipe_id == recipe.c.id, full=True)
        )
        if pk:
            query = query.where(recipe.c.id == pk)
        query = await self.database.fetch_all(query)

        if not query:
            return None

        query = [dict(i) for i in query]
        for r in query:
            r["ingredients"] = await Amount.get_amount_by_recipe_id(
                self, r["id"])
            r["tags"] = await Tag.get_tags_by_recipe_id(self, r["id"])
            r["author"] = await User.get_user_full_by_id_auth(
                self, r["author"], auth)
        return query

    async def delete_recipe(self, pk: int):
        query = recipe.delete().where(recipe.c.id == pk)
        await self.database.execute(query)
