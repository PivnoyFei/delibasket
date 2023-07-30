import os

from starlette.requests import Request

from application.schemas import Params
from application.settings import MEDIA_ROOT


async def get_result(request: Request, count: int, params: Params, results: list) -> dict:
    """
    Составляет json ответ для пользователя в соответствии с требованиями.
    Составляет следующую, предыдущую и количество страниц для пагинации.
    """
    page = params.page
    if count and count > 0:
        return {
            "count": count,
            "next": (
                str(request.url.replace_query_params(page=page + 1))
                if page * params.limit < count
                else None
            ),
            "previous": str(request.url.replace_query_params(page=page - 1)) if page > 1 else None,
            "results": results,
        }
    return {"count": 0, "next": None, "previous": None, "results": []}


async def image_delete(filename: str = "", image_path: str = "") -> None:
    if not image_path:
        image_path = os.path.join(MEDIA_ROOT, filename)
    if os.path.isfile(image_path):
        os.remove(image_path)
