"""Exception handlers para consistent ang API error responses."""

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import error_response


async def api_http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Converts FastAPI HTTPException into the project's standard error shape."""
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        content = exc.detail
    else:
        content = error_response("HTTP_ERROR", str(exc.detail))

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


async def api_request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Ginagawang field map ang Pydantic errors para madaling gamitin ng frontend."""
    fields: dict[str, str] = {}
    for validation_error in exc.errors():
        location = validation_error["loc"]
        field_parts = [str(part) for part in location if part != "body"]
        field_name = ".".join(field_parts) or "request"
        fields.setdefault(field_name, validation_error["msg"])

    return JSONResponse(
        status_code=422,
        content=error_response(
            "VALIDATION_ERROR",
            "Some fields are invalid.",
            fields,
        ),
    )
