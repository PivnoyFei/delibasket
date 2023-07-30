from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.recipes.schemas import TagOut
from application.tags.models import Tag, recipe_tag


class TagManager:
    @staticmethod
    async def get_tags_by_id(session: AsyncSession, pk: int) -> list[TagOut]:
        tags_dict = await session.execute(
            select(Tag.id, Tag.name, Tag.color, Tag.slug)
            .join(recipe_tag, recipe_tag.c.tag_id == Tag.id)
            .where(recipe_tag.c.recipe_id == pk)
            .order_by(Tag.id)
        )
        return tags_dict.all()
