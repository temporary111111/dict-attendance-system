"""Standard API response shapes.

Pare-pareho dapat ang success at error responses para madali gamitin ng frontend.
"""

from typing import Any


def success_response(data: Any, message: str) -> dict[str, Any]:
    """Standard success format ng API."""
    return {
        "data": data,
        "message": message,
    }


def error_response(
    code: str,
    message: str,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standard error format ng API, kasama ang optional field-level errors."""
    return {
        "error": {
            "code": code,
            "message": message,
            "fields": fields or {},
        }
    }
