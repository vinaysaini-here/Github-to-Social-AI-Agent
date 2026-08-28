import uuid
from pathlib import Path

from social_agent.config import get_settings

MEDIA_SUBDIR = "media"


def save_media_bytes(content: bytes, original_filename: str | None) -> Path:
    """Save file bytes to the media directory, return the path it was saved to."""
    settings = get_settings()
    media_dir = Path(settings.output_dir).parent / MEDIA_SUBDIR
    media_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(original_filename or "").suffix
    stored_name = f"{uuid.uuid4().hex}{extension}"
    destination = media_dir / stored_name
    destination.write_bytes(content)
    return destination