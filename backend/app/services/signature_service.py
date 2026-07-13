"""Private verification at storage ng attendee signature images."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError


class InvalidSignatureImageError(Exception):
    """Raised kapag unsupported, oversized, o invalid ang uploaded image."""


def save_signature_image(
    upload: UploadFile,
    directory: Path,
    event_id: int,
    max_bytes: int,
) -> str:
    """Vine-verify at nire-reencode as PNG para alisin ang image metadata."""
    if upload.content_type not in {"image/png", "image/jpeg"}:
        raise InvalidSignatureImageError

    raw_bytes = upload.file.read(max_bytes + 1)
    if not raw_bytes or len(raw_bytes) > max_bytes:
        raise InvalidSignatureImageError

    try:
        with Image.open(BytesIO(raw_bytes)) as verification_image:
            verification_image.verify()
        with Image.open(BytesIO(raw_bytes)) as source_image:
            source_image.load()
            if source_image.width > 3000 or source_image.height > 3000:
                raise InvalidSignatureImageError
            normalized_image = source_image.convert("RGBA")

            relative_directory = Path(f"event-{event_id}")
            filename = f"signature-{uuid4().hex}.png"
            final_directory = directory / relative_directory
            final_directory.mkdir(parents=True, exist_ok=True)
            final_path = final_directory / filename
            temporary_path = final_directory / f".{filename}.tmp"
            normalized_image.save(temporary_path, format="PNG", optimize=True)
            temporary_path.replace(final_path)
            return (relative_directory / filename).as_posix()
    except (Image.DecompressionBombError, OSError, UnidentifiedImageError) as exc:
        raise InvalidSignatureImageError from exc


def remove_signature_image(directory: Path, relative_path: str | None) -> None:
    if not relative_path:
        return
    candidate = directory / Path(relative_path)
    try:
        candidate.resolve().relative_to(directory.resolve())
        candidate.unlink(missing_ok=True)
    except (OSError, ValueError):
        return
