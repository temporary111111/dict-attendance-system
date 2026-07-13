from io import BytesIO

import pytest
from fastapi import UploadFile
from PIL import Image

from app.services.signature_service import (
    InvalidSignatureImageError,
    remove_signature_image,
    save_signature_image,
)


def make_upload(
    content: bytes,
    *,
    filename: str = "signature.png",
    content_type: str = "image/png",
) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers={"content-type": content_type},
    )


def make_image_bytes(image_format: str = "PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (80, 30), "white").save(buffer, format=image_format)
    return buffer.getvalue()


def test_save_signature_rejects_unsupported_content_type(tmp_path):
    upload = make_upload(
        make_image_bytes(),
        content_type="image/gif",
    )

    with pytest.raises(InvalidSignatureImageError):
        save_signature_image(upload, tmp_path, event_id=5, max_bytes=1024)


def test_save_signature_rejects_file_over_size_limit(tmp_path):
    upload = make_upload(make_image_bytes())

    with pytest.raises(InvalidSignatureImageError):
        save_signature_image(upload, tmp_path, event_id=5, max_bytes=10)


def test_save_signature_normalizes_jpeg_to_private_png(tmp_path):
    upload = make_upload(
        make_image_bytes("JPEG"),
        filename="signature.jpg",
        content_type="image/jpeg",
    )

    relative_path = save_signature_image(
        upload,
        tmp_path,
        event_id=5,
        max_bytes=1024 * 1024,
    )

    saved_path = tmp_path / relative_path
    assert relative_path.startswith("event-5/signature-")
    assert saved_path.suffix == ".png"
    with Image.open(saved_path) as image:
        assert image.format == "PNG"
        assert image.mode == "RGBA"


def test_remove_signature_does_not_delete_outside_private_directory(tmp_path):
    private_directory = tmp_path / "private"
    private_directory.mkdir()
    outside_file = tmp_path / "outside.png"
    outside_file.write_bytes(b"outside")

    remove_signature_image(private_directory, "../outside.png")

    assert outside_file.read_bytes() == b"outside"
