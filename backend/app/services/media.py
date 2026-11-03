"""Safe image uploads.

Uploaded files are never stored as-is: the bytes are decoded with Pillow (rejecting anything
that is not a real JPEG/PNG/WebP image), downscaled, and re-encoded to WebP under a random
filename. This strips metadata and neutralises polyglot/malicious payloads.
"""

import io
import secrets

from fastapi import UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings
from app.core.errors import AppError
from app.schemas.admin import UploadOut

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_DIMENSION = 1600
MAX_PIXELS = 40_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


async def save_food_image(upload: UploadFile) -> UploadOut:
    data = await upload.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise AppError(
            status.HTTP_413_CONTENT_TOO_LARGE,
            "FILE_TOO_LARGE",
            f"Images must be {settings.max_upload_mb} MB or smaller.",
        )
    if not data:
        raise AppError(status.HTTP_400_BAD_REQUEST, "EMPTY_FILE", "The file is empty.")

    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            probe.verify()
        if fmt not in ALLOWED_FORMATS:
            raise UnidentifiedImageError(fmt)
        image = Image.open(io.BytesIO(data))
        image = ImageOps.exif_transpose(image)
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
        image = image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB")
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as exc:
        raise AppError(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "INVALID_IMAGE",
            "Please upload a JPEG, PNG or WebP image.",
        ) from exc

    folder = settings.media_root / "foods"
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{secrets.token_hex(12)}.webp"
    out = io.BytesIO()
    image.save(out, format="WEBP", quality=82, method=4)
    (folder / filename).write_bytes(out.getvalue())

    return UploadOut(
        url=f"{settings.media_url_prefix}/foods/{filename}",
        width=image.width,
        height=image.height,
        size_bytes=out.tell(),
    )
