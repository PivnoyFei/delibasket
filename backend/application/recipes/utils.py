import base64
import binascii
import os
from uuid import uuid4

import aiofiles
from starlette.exceptions import HTTPException
from starlette.status import HTTP_418_IM_A_TEAPOT

from application.settings import ALLOWED_TYPES, INVALID_FILE, INVALID_TYPE, MEDIA_ROOT


async def base64_image(base64_data: str, extension: str = "jpg") -> tuple[str, str]:
    """
    Проверяет формат файла если он есть.
    При удачном декодировании base64, файл будет сохранен.
    """
    if ";base64," in base64_data:
        header, base64_data = base64_data.split(";base64,")
        name, extension = header.split("/")
        if extension.lower() not in ALLOWED_TYPES:
            raise HTTPException(HTTP_418_IM_A_TEAPOT, INVALID_TYPE)

    filename = f"{uuid4()}.{extension}"
    image_path = os.path.join(MEDIA_ROOT, filename)

    try:
        async with aiofiles.open(image_path, "wb") as buffer:
            await buffer.write(base64.b64decode(base64_data))

    except (Exception, TypeError, binascii.Error, ValueError):
        raise HTTPException(HTTP_418_IM_A_TEAPOT, INVALID_FILE)

    return filename, image_path
