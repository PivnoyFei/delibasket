from typing import Any

import sqlalchemy as sa
from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from starlette.requests import Request

from application.database import Base
from application.recipes.schemas import (
    AmountOut,
    FavoriteOut,
    QueryParams,
    RecipeOut,
    SAmountIngredient,
    SIngredient,
    STag,
    TagOut,
)
from application.settings import MEDIA_URL
from application.users.managers import UserDB

TypeTagDB = TagOut | list[TagOut] | None


class Ingredient(Base):
    __table_args__ = (sa.UniqueConstraint('name', 'measurement_unit'),)

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(200), unique=True, index=True)
    measurement_unit = sa.Column(sa.String(200))


class Tag(Base):
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(200), unique=True, index=True)
    color = sa.Column(sa.String(6), unique=True)
    slug = sa.Column(sa.String(200), unique=True, index=True)


class Recipe(Base):
    __table_args__ = (sa.CheckConstraint('cooking_time > 0'),)

    id = sa.Column(sa.Integer, primary_key=True)
    author_id = sa.Column(sa.Integer, sa.ForeignKey("user.id", ondelete='CASCADE'))
    name = sa.Column(sa.String(200), unique=True, index=True)
    image = sa.Column(sa.String(200), unique=True)
    text = sa.Column(sa.Text)
    cooking_time = sa.Column(sa.Integer)
    pub_date = sa.Column(sa.DateTime(timezone=True), default=func.now())


class RecipeTag(Base):
    __table_args__ = (sa.UniqueConstraint('recipe_id', 'tag_id'),)

    id = sa.Column(sa.Integer, primary_key=True)
    recipe_id = sa.Column(sa.Integer, sa.ForeignKey("recipe.id", ondelete='CASCADE'))
    tag_id = sa.Column(sa.Integer, sa.ForeignKey("tag.id", ondelete='CASCADE'))


class Favorite(Base):
    __table_args__ = (sa.UniqueConstraint('user_id', 'recipe_id'),)

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id", ondelete='CASCADE'))
    recipe_id = sa.Column(sa.Integer, sa.ForeignKey("recipe.id", ondelete='CASCADE'))


class Cart(Base):
    __table_args__ = (sa.UniqueConstraint('user_id', 'recipe_id'),)

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id", ondelete='CASCADE'))
    recipe_id = sa.Column(sa.Integer, sa.ForeignKey("recipe.id", ondelete='CASCADE'))


class AmountIngredient(Base):
    __table_args__ = (
        sa.UniqueConstraint('ingredient_id', 'recipe_id'),
        sa.CheckConstraint('amount > 0'),
    )

    id = sa.Column(sa.Integer, primary_key=True)
    recipe_id = sa.Column(sa.Integer, sa.ForeignKey("recipe.id", ondelete='CASCADE'))
    ingredient_id = sa.Column(sa.Integer, sa.ForeignKey("ingredient.id", ondelete='CASCADE'))
    amount = sa.Column(sa.Integer)


class TagDB:
    @staticmethod
    async def create(session: AsyncSession, items: STag) -> Tag | UniqueViolationError:
        try:
            query = await session.execute(
                sa.insert(Tag)
                .values(
                    name=items.name,
                    color=items.color,
                    slug=items.slug,
                )
                .returning(Tag)
            )
            await session.commit()
            return query.scalar()
        except UniqueViolationError as e:
            return e

    @staticmethod
    async def get(session: AsyncSession, pk: int | None = None, name: str = "") -> TypeTagDB:
        query = sa.select(Tag.id, Tag.name, Tag.color, Tag.slug)
        if pk:
            query = await session.execute(query.where(Tag.id == pk))
            return query.one()
        else:
            if name:
                query = query.where(Tag.name.like(f"{name}%"))
        query = await session.execute(query)
        return query.all()

    @staticmethod
    async def get_tags_by_recipe_id(session: AsyncSession, pk: int) -> list[TagOut]:
        tags_dict = await session.execute(
            sa.select(Tag.id, Tag.name, Tag.color, Tag.slug)
            .join(RecipeTag, RecipeTag.tag_id == Tag.id)
            .where(RecipeTag.recipe_id == pk)
            .order_by(Tag.id)
        )
        return tags_dict.all()

    @staticmethod
    async def update(session: AsyncSession, items: STag, pk: int) -> Any:
        try:
            query = await session.execute(
                sa.update(Tag).values(**dict(items)).where(Tag.id == pk).returning(Tag)
            )
            await session.commit()
            return dict(query.all()[0])

        except (ProgrammingError, IndexError) as e:
            await session.rollback()
            return e

    @staticmethod
    async def delete(session: AsyncSession, pk: int) -> bool | None:
        await session.execute(sa.delete(Tag).where(Tag.id == pk))
        await session.commit()
        return True


class IngredientDB:
    @staticmethod
    async def create(session: AsyncSession, items: SIngredient) -> Ingredient:
        try:
            query = await session.execute(
                sa.insert(Ingredient)
                .values(
                    name=items.name,
                    measurement_unit=items.measurement_unit,
                )
                .returning(Ingredient)
            )
            await session.commit()
            return query.scalar()

        except UniqueViolationError as e:
            return e

    @staticmethod
    async def get(session: AsyncSession, pk: int | None = None, name: str = "") -> Any:
        query = sa.select(Ingredient.id, Ingredient.name, Ingredient.measurement_unit)
        if pk:
            query = await session.execute(query.where(Ingredient.id == pk))
            return query.one()
        else:
            if name:
                query = query.where(Ingredient.name.like(f"{name}%"))
        query = await session.execute(query.limit(20))
        return query.all()

    @staticmethod
    async def update(session: AsyncSession, items: SIngredient, pk: int) -> Any:
        try:
            query = await session.execute(
                sa.update(Ingredient)
                .values(**dict(items))
                .where(Ingredient.id == pk)
                .returning(Ingredient)
            )
            await session.commit()
            return dict(query.all()[0])

        except (ProgrammingError, IndexError) as e:
            await session.rollback()
            return e

    async def delete(session: AsyncSession, pk: int) -> bool | None:
        await session.execute(sa.delete(Ingredient).where(Ingredient.id == pk))
        await session.commit()
        return True


class AmountDB:
    @staticmethod
    async def get_amount_by_recipe_id(session: AsyncSession, pk: int) -> list[AmountOut]:
        amount_dict = await session.execute(
            sa.select(
                Ingredient.id,
                Ingredient.name,
                Ingredient.measurement_unit,
                AmountIngredient.amount,
            )
            .join(Ingredient, AmountIngredient.ingredient_id == Ingredient.id)
            .where(AmountIngredient.recipe_id == pk)
        )
        return amount_dict.all()


class RecipeDB:
    @staticmethod
    async def _create_recipe_tag(session: AsyncSession, recipe_id: int, tags: list) -> Any:
        tags = [{"recipe_id": recipe_id, "tag_id": i} for i in tags]
        return await session.execute(sa.insert(RecipeTag).values(tags))

    @staticmethod
    async def _create_amount_ingredient(
        session: AsyncSession, recipe_id: int, ingredients: list
    ) -> Any:
        result = [
            {"recipe_id": recipe_id, "ingredient_id": i["id"], "amount": int(i["amount"])}
            for i in ingredients
        ]
        return await session.execute(sa.insert(AmountIngredient).values(result))

    @staticmethod
    async def create(
        session: AsyncSession,
        recipe_item: dict,
        ingredients: list[SAmountIngredient],
        tags: list[int],
    ) -> Any:
        try:
            recipe_id = await session.scalar(
                sa.insert(Recipe).values(**recipe_item).returning(Recipe.id)
            )
            await RecipeDB._create_recipe_tag(session, recipe_id, tags)
            await RecipeDB._create_amount_ingredient(session, recipe_id, ingredients)
            await session.commit()
            return recipe_id

        except (UniqueViolationError, AttributeError) as e:
            await session.rollback()
            return e

    @staticmethod
    async def check_author_by_id(session: AsyncSession, pk: int) -> int:
        query = await session.execute(sa.select(Recipe.author_id).where(Recipe.id == pk))
        return query.scalar()

    @staticmethod
    async def check_recipe_author_image_by_id(session: AsyncSession, pk: int) -> tuple[int, str]:
        query = await session.execute(
            sa.select(Recipe.author_id, Recipe.image).where(Recipe.id == pk)
        )
        return query.one()

    @staticmethod
    async def check_recipe_by_id_author(
        session: AsyncSession,
        request: Request,
        recipe_id: int | None = None,
        author_id: int | None = None,
        limit: int | None = None,
        page: int | None = None,
    ) -> list[FavoriteOut] | None:
        query = sa.select(Recipe.id, Recipe.name, Recipe.image, Recipe.cooking_time)
        if author_id:
            query = query.where(Recipe.author_id == author_id).order_by(Recipe.pub_date.desc())
        if recipe_id:
            query = query.where(Recipe.id == recipe_id)
        else:
            if limit:
                query = query.limit(limit)
                if page:
                    query = query.offset((page - 1) * limit)
        recipes = await session.execute(query)
        recipe_all = recipes.all()

        if recipe_all:
            path_image = f"{request.base_url}{MEDIA_URL}"
            recipe_all = [dict(i) for i in recipe_all]
            for recipe in recipe_all:
                recipe["image"] = path_image + recipe["image"]
        return recipe_all[0] if recipe_id else recipe_all

    @staticmethod
    async def count_recipe(
        session: AsyncSession,
        author: int | None = None,
        tags: QueryParams | None = None,
        is_favorited: bool | None = True,
        is_in_cart: bool | None = True,
    ) -> int:
        query = (
            sa.select(func.count(Recipe.id).label("is_count"))
            .join(Favorite, Favorite.recipe_id == Recipe.id, isouter=is_favorited)
            .join(Cart, Cart.recipe_id == Recipe.id, isouter=is_in_cart)
        )
        if author:
            query = query.where(Recipe.author_id == author)
        if tags and tags.tags:
            query = (
                query.join(RecipeTag, RecipeTag.recipe_id == Recipe.id)
                .join(Tag, RecipeTag.tag_id == Tag.id)
                .where(Tag.slug.in_(tags.tags))
                .group_by(Tag.slug)
                .distinct()
            )
        count = await session.execute(query)
        return count.scalar() if count else 0

    @staticmethod
    async def get(
        session: AsyncSession,
        request: Request,
        pk: int | None = None,
        tags: QueryParams | None = None,
        page: int | None = None,
        limit: int | None = 6,
        author: int | None = None,
        is_favorited: bool = True,
        is_in_cart: bool = True,
        user_id: int | None = None,
    ) -> list[RecipeOut] | None:
        if tags and not tags.tags and is_in_cart:
            return []
        query = (
            sa.select(
                Recipe.id,
                Recipe.name,
                Recipe.image,
                Recipe.author_id.label("author"),
                Recipe.text,
                Recipe.cooking_time,
                sa.case(
                    (sa.and_(user_id != None, Favorite.user_id == user_id), "True"), else_="False"
                ).label("is_favorited"),
                sa.case(
                    (sa.and_(user_id != None, Cart.user_id == user_id), "True"), else_="False"
                ).label("is_in_shopping_cart"),
            )
            .join(Favorite, Favorite.recipe_id == Recipe.id, isouter=is_favorited)
            .join(Cart, Cart.recipe_id == Recipe.id, isouter=is_in_cart)
            .order_by(Recipe.pub_date.desc())
            # .distinct()
        )
        if pk:
            query = query.where(Recipe.id == pk)
        else:
            if author:
                query = query.where(Recipe.author_id == author)
            if tags and tags.tags:
                query = (
                    query.join(RecipeTag, RecipeTag.recipe_id == Recipe.id, isouter=True)
                    .join(Tag, RecipeTag.tag_id == Tag.id, isouter=True)
                    .where(Tag.slug.in_(tags.tags))
                    .group_by(Recipe.id, Favorite.user_id, Cart.user_id)
                    .having(func.count(Tag.slug) <= len(tags.tags))
                )
            if limit:
                query = query.limit(limit)
                if page:
                    query = query.offset((page - 1) * limit)

        recipes = await session.execute(query)
        recipe_all = recipes.all()
        if not recipe_all:
            return []

        recipe_all = [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": recipe.image,
                "author": recipe.author,
                "text": recipe.text,
                "cooking_time": recipe.cooking_time,
                "is_favorited": recipe.is_favorited,
                "is_in_shopping_cart": recipe.is_in_shopping_cart,
            }
            for recipe in recipe_all
        ]
        # recipe_all = [dict(i) for i in recipe_all]

        path_image = f"{request.base_url}{MEDIA_URL}/"
        for recipe in recipe_all:
            recipe["image"] = path_image + recipe["image"]
            recipe["ingredients"] = await AmountDB.get_amount_by_recipe_id(session, recipe["id"])
            recipe["tags"] = await TagDB.get_tags_by_recipe_id(session, recipe["id"])
            if user_id:
                recipe["author"] = await UserDB.user_by_id_auth(session, recipe["author"], user_id)
        return recipe_all

    @staticmethod
    async def update(
        session: AsyncSession,
        pk: int,
        recipe_item: dict,
        ingredients: list[SAmountIngredient],
        tags: list[int],
    ) -> int | None:
        try:
            recipe_id = await session.scalar(
                sa.update(Recipe).values(**recipe_item).where(Recipe.id == pk).returning(Recipe.id)
            )
            await session.execute(sa.delete(RecipeTag).where(RecipeTag.recipe_id == pk))
            await RecipeDB._create_recipe_tag(session, recipe_id, tags)

            await session.execute(
                sa.delete(AmountIngredient).where(AmountIngredient.recipe_id == pk)
            )
            await RecipeDB._create_amount_ingredient(session, recipe_id, ingredients)
            await session.commit()
            return recipe_id

        except:
            await session.rollback()
            return None

    @staticmethod
    async def delete(session: AsyncSession, pk: int) -> None:
        await session.execute(sa.delete(Recipe).where(Recipe.id == pk))
        await session.commit()


class FavoriteCartDB:
    @staticmethod
    async def get_shopping_cart(session: AsyncSession, user_id: int) -> list:
        query = await session.execute(
            sa.select(
                Ingredient.name,
                Ingredient.measurement_unit,
                func.sum(AmountIngredient.amount).label("amount"),
            )
            .filter(Cart.recipe_id == AmountIngredient.recipe_id)
            .join(Ingredient, AmountIngredient.ingredient_id == Ingredient.id)
            .where(Cart.user_id == user_id)
            .group_by(Ingredient.name, Ingredient.measurement_unit)
        )
        return query.all()

    @staticmethod
    async def create(
        session: AsyncSession, recipe_id: int, user_id: int, db_model: Favorite | Cart
    ) -> bool:
        try:
            await session.execute(sa.insert(db_model).values(recipe_id=recipe_id, user_id=user_id))
            await session.commit()
            return True
        except UniqueViolationError:
            return False

    @staticmethod
    async def delete(
        session: AsyncSession, recipe_id: int, user_id: int, db_model: Favorite | Cart
    ) -> bool:
        try:
            await session.execute(
                sa.delete(db_model).where(
                    db_model.recipe_id == recipe_id, db_model.user_id == user_id
                )
            )
            await session.commit()
            return True
        except:
            return False
