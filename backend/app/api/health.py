"""Health check routes para malaman kung buhay ang API at DB connection."""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.responses import error_response, success_response
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def read_health() -> dict[str, Any]:
    """Basic API check; hindi nito tine-test ang database."""
    return success_response({"status": "ok"}, "API is running.")


@router.get("/db", response_model=None)
def read_database_health(db: Session = Depends(get_db)) -> dict[str, Any] | JSONResponse:
    """Database check gamit ang lightweight SELECT 1 query."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content=error_response(
                "DATABASE_UNAVAILABLE",
                "Database connection is unavailable.",
            ),
        )

    return success_response(
        {"database": "ok"},
        "Database connection is available.",
    )
