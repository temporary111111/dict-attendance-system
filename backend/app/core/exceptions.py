"""Exception handlers para consistent ang API error responses."""

from fastapi import HTTPException, Request
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
