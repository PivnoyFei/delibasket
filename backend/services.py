import os

from settings import MEDIA_ROOT
from starlette.requests import Request


async def query_list(
    query: list,
    request: Request,
    count: int = 0,
    page: int = 1,
    limit: int = 6,
) -> dict:
    """
    Составляет json ответ для пользователя в соответствии с требованиями.
    Составляет следующую, предыдущую и количество страниц для пагинации.
    """
    next_page = (
        str(request.url).replace(f"page={page}", f"page={page + 1}")
        if page and page * limit < count else None
    )
    previous = (
        str(request.url).replace(f"page={page}", f"page={page - 1}")
        if page and page > 1 else None
    )
    return {
        "count": count,
        "next": next_page,
        "previous": previous,
        "results": query
    }


async def image_delete(filename: str = "", image_path: str = "") -> None:
    if not image_path:
        image_path = os.path.join(MEDIA_ROOT, filename)
    if os.path.isfile(image_path):
        os.remove(image_path)
