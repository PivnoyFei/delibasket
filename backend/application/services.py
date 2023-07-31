import os

from application.settings import MEDIA_ROOT


async def image_delete(filename: str = "", image_path: str = "") -> None:
    if not image_path:
        image_path = os.path.join(MEDIA_ROOT, filename)
    if os.path.isfile(image_path):
        os.remove(image_path)
