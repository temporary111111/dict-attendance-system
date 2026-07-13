"""Filesystem helper para sa locally generated attendance QR codes."""

from pathlib import Path

import qrcode


class QRCodeGenerationError(Exception):
    """Raised kapag hindi maisulat ang QR PNG sa configured storage."""


def generate_qr_png(
    data: str,
    directory: Path,
    filename: str,
) -> Path:
    """Atomically nagsusulat ng QR PNG para walang partial file na ma-serve."""
    if Path(filename).name != filename:
        raise QRCodeGenerationError("Invalid QR filename.")

    try:
        directory.mkdir(parents=True, exist_ok=True)
        final_path = directory / filename
        temporary_path = directory / f".{filename}.tmp"
        image = qrcode.make(data)
        image.save(temporary_path, format="PNG")
        temporary_path.replace(final_path)
        return final_path
    except (OSError, ValueError) as exc:
        raise QRCodeGenerationError from exc


def remove_qr_png(directory: Path, public_path: str | None) -> None:
    """Filename lang ang ginagamit para hindi makalabas sa QR directory."""
    if not public_path:
        return
    filename = Path(public_path).name
    try:
        (directory / filename).unlink(missing_ok=True)
    except OSError:
        # Cleanup failure should not undo an already committed event update.
        return
