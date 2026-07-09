from typing import Any


def success_response(data: Any, message: str) -> dict[str, Any]:
    return {
        "data": data,
        "message": message,
    }


def error_response(
    code: str,
    message: str,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "fields": fields or {},
        }
    }
