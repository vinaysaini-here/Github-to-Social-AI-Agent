from fastapi import UploadFile

from social_agent.config import get_settings

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "video/mp4", "video/quicktime", "video/webm",
}


class MediaValidationError(ValueError):
    """Raised when an uploaded file fails basic media guardrails."""


async def validate_media_upload(upload: UploadFile) -> bytes:
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise MediaValidationError(f"unsupported file type: {upload.content_type}")

    settings = get_settings()
    max_bytes = settings.max_media_size_mb * 1024 * 1024

    content = await upload.read()
    if len(content) > max_bytes:
        raise MediaValidationError(f"file exceeds {settings.max_media_size_mb}MB limit")

    return content