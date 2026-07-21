"""Save, replace, and delete program logo image files."""

import uuid
from pathlib import Path

from fastapi import UploadFile


ALLOWED_CONTENT_TYPES = frozenset({"image/png", "image/jpeg"})
ALLOWED_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg"})


class InvalidProgramLogoError(Exception):
    """Raised kapag invalid ang uploaded logo file."""


def save_program_logo(
    upload: UploadFile,
    logo_directory: Path,
    max_bytes: int,
) -> str:
    """Sine-save ang uploaded logo file; ibinabalik ang stored filename."""
    content_type = (upload.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise InvalidProgramLogoError(
            "Upload a valid PNG or JPEG logo image."
        )

    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        suffix = ".png" if "png" in content_type else ".jpg"

    data = upload.file.read()
    if len(data) == 0:
        raise InvalidProgramLogoError("The uploaded logo file is empty.")
    if len(data) > max_bytes:
        mb = max_bytes // (1024 * 1024)
        raise InvalidProgramLogoError(
            f"Logo file must be under {mb} MB. Upload a smaller image."
        )

    logo_directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    (logo_directory / filename).write_bytes(data)
    return filename


def delete_program_logo(logo_directory: Path, filename: str | None) -> None:
    """Tahimik na dinedemet ang logo file kung meron."""
    if not filename:
        return
    (logo_directory / filename).unlink(missing_ok=True)
