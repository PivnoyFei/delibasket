import os

from starlette.requests import Request

from settings import MEDIA_ROOT


async def query_list(
    query: list = [],
    request: Request = None,
    count: int | None = 0,
    page: int | None = None,
    limit: int | None = None
):
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


async def image_delete(filename=None, image_path=""):
    if not image_path:
        image_path = os.path.join(MEDIA_ROOT, filename)
    if os.path.isfile(image_path):
        os.remove(image_path)
