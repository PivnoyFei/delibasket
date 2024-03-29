import logging
from datetime import datetime

from asyncpg.exceptions import UniqueViolationError
from sqlalchemy import Result, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from starlette.requests import Request

from application.database import scoped_session
from application.managers import BaseManager
from application.recipes.models import Cart, Favorite, Recipe
from application.recipes.schemas import CreateRecipe, FavoriteOut, RecipeOut, UpdateRecipe
from application.schemas import SearchRecipe
from application.services import (
    delete_is_ingredients,
    get_is_ingredients,
    get_shopping_cart,
    post_is_ingredients,
    update_is_ingredients,
)
from application.tags.models import Tag, recipe_tag
from application.users.managers import UserManager
from application.users.models import User

logger = logging.getLogger(__name__)


class RecipeManager:
    @staticmethod
    async def _create_recipe_tag(session: AsyncSession, tags: list) -> Result:
        return await session.execute(insert(recipe_tag).values(tags))

    @staticmethod
    async def session_is_favorited(
        session: AsyncSession,
        recipe_id: int,
        user_id: int,
    ) -> int | None:
        query = await session.execute(
            select(Favorite.id).where(
                Favorite.recipe_id == recipe_id,
                Favorite.user_id == user_id,
            )
        )
        return query.one_or_none()

    @staticmethod
    async def session_is_cart(session: AsyncSession, recipe_id: int, user_id: int) -> int | None:
        query = await session.execute(
            select(Cart.id).where(
                Cart.recipe_id == recipe_id,
                Cart.user_id == user_id,
            )
        )
        return query.one_or_none()

    async def create(self, items: dict, recipe_in: CreateRecipe) -> int | None:
        async with scoped_session() as session:
            try:
                recipe_id = await session.scalar(
                    insert(Recipe).values(**items).returning(Recipe.id)
                )
                await self._create_recipe_tag(session, await recipe_in.tags_to_list(recipe_id))
                if await post_is_ingredients(
                    {
                        "id": recipe_id,
                        "ingredients": await recipe_in.ingredients_to_list(recipe_id),
                    }
                ):
                    await session.commit()
                    return recipe_id
                raise AttributeError

            except (UniqueViolationError, AttributeError) as e:
                await session.rollback()
                await delete_is_ingredients(recipe_id)
                logger.error(e)
                return None

    async def update(self, pk: int, items: dict, recipe_in: UpdateRecipe) -> int | None:
        async with scoped_session() as session:
            try:
                recipe_id = await session.scalar(
                    update(Recipe)
                    .values(**items, updated_at=datetime.utcnow())
                    .where(Recipe.id == pk)
                    .returning(Recipe.id)
                )
                await session.execute(delete(recipe_tag).where(recipe_tag.c.recipe_id == pk))
                await self._create_recipe_tag(session, await recipe_in.tags_to_list(recipe_id))

                if await update_is_ingredients(
                    {"id": recipe_id, "ingredients": await recipe_in.ingredients_to_list(recipe_id)}
                ):
                    await session.commit()
                    return recipe_id
                raise AttributeError

            except Exception as e:
                await session.rollback()
                logger.error(e)
                return None

    async def author_by_id(self, pk: int) -> int:
        async with scoped_session() as session:
            query = await session.execute(select(Recipe.author_id).where(Recipe.id == pk))
            return query.one()

    async def get(self, request: Request, pk: int) -> dict:
        async with scoped_session() as session:
            user_id = request.user.id
            query = await session.execute(
                select(
                    *Recipe.list_columns("id", "name", "text", "cooking_time"),
                    Recipe.image_path(request),
                    Recipe.author_id.label("author"),
                    Tag.array_agg("id", "name", "color", "slug").label("tags"),
                )
                .join(Recipe.tags, isouter=True)
                .where(Recipe.id == pk)
                .group_by(Recipe.id)
            )
            recipe = query.one_or_none()

            if not recipe:
                return recipe

            recipe_dict = await RecipeOut.to_dict(  # TODO описание проблемы внутри
                recipe,
                author=await UserManager.session_by_id(session, recipe.author, user_id),
                is_favorited=await self.session_is_favorited(session, recipe.id, user_id),
                is_in_shopping_cart=await self.session_is_cart(session, recipe.id, user_id),
            )
            if ingredients := await get_is_ingredients(recipe.id):
                recipe_dict["ingredients"] = ingredients
                return recipe_dict

            raise AttributeError

    async def get_all(self, request: Request, params: SearchRecipe) -> tuple[int, list]:
        async with scoped_session() as session:
            user_id = request.user.id
            query = (
                select(
                    *Recipe.list_columns("id", "name", "text", "cooking_time"),
                    Recipe.image_path(request),
                    User.json_build_object(
                        "id",
                        "email",
                        "username",
                        "first_name",
                        "last_name",
                    ).label("author"),
                    Tag.array_agg("id", "name", "color", "slug").label("tags"),
                )
                .join(Recipe.author)
                .group_by(Recipe.id, User.id)
                .order_by(Recipe.pub_date.desc(), Recipe.created_at.desc())
            )
            count, query = await params.search(query)

            if user_id and not params.is_favorited:
                count, query = [
                    row.join(Recipe.favorites, isouter=params.is_favorited).where(
                        Favorite.user_id == user_id
                    )
                    for row in (count, query)
                ]
                query = query.group_by(Favorite.user_id)
            if user_id and not params.is_in_shopping_cart:
                count, query = [
                    row.join(Recipe.carts, isouter=params.is_in_shopping_cart).where(
                        Cart.user_id == user_id
                    )
                    for row in (count, query)
                ]
                query = query.group_by(Cart.user_id)

            if params.tags:
                query = (
                    query.join(Recipe.tags, isouter=True)
                    .where(Tag.slug.in_(params.tags))
                    .having(func.count(Tag.slug) == len(params.tags))
                )
                count = (
                    count.join(Recipe.tags, isouter=True)
                    .where(Tag.slug.in_(params.tags))
                    .group_by(Tag.slug)
                    .distinct()
                )

            count = await session.scalar(count)
            if not count:
                return 0, []

            query = await session.execute(query)
            all_recipe = [
                await RecipeOut.to_dict(  # TODO описание проблемы внутри
                    recipe,
                    is_favorited=await self.session_is_favorited(session, recipe.id, user_id),
                    is_in_shopping_cart=await self.session_is_cart(session, recipe.id, user_id),
                )
                for recipe in query.all()
            ]
            return count, all_recipe


class FavoriteCartManager(BaseManager):
    @staticmethod
    async def get_shopping_cart(user_id: int) -> list:
        async with scoped_session() as session:
            query = await session.execute(select(Cart.recipe_id).where(Cart.user_id == user_id))
            return await get_shopping_cart(query.scalars().all())

    async def create(self, request: Request, recipe_id: int, user_id: int) -> FavoriteOut | None:
        async with scoped_session() as session:
            recipe = await session.execute(
                select(
                    Recipe.id, Recipe.name, Recipe.image_path(request), Recipe.cooking_time
                ).where(Recipe.id == recipe_id)
            )
            if recipe:
                try:
                    await session.execute(
                        insert(self.model).values(
                            recipe_id=recipe_id,
                            user_id=user_id,
                        )
                    )
                    await session.commit()
                    return recipe.one_or_none()
                except UniqueViolationError as e:
                    logger.error(e)

            return None

    async def delete(self, recipe_id: int, user_id: int) -> bool:
        async with scoped_session() as session:
            try:
                await session.execute(
                    delete(self.model).where(
                        self.model.recipe_id == recipe_id,
                        self.model.user_id == user_id,
                    )
                )
                await session.commit()
                return True
            except Exception as e:
                logger.error(e)
                return False
