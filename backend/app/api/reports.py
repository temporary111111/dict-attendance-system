"""Dashboard at role-scoped report endpoints."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.models import User
from app.schemas.reports import (
    DashboardSummaryResponse,
    EventAttendanceReportResponse,
    ProgramSummaryResponse,
)
from app.services.report_service import (
    InvalidReportDateRangeError,
    ReportAccessDeniedError,
    ReportEventNotFoundError,
    ReportProgramNotFoundError,
    get_dashboard_summary,
    get_event_attendance_report,
    get_program_summary,
)

router = APIRouter(tags=["dashboard and reports"])


def _raise_report_error(exc: Exception) -> None:
    if isinstance(exc, ReportProgramNotFoundError):
        raise HTTPException(
            status_code=404,
            detail=error_response("PROGRAM_NOT_FOUND", "Program not found."),
        )
    if isinstance(exc, ReportEventNotFoundError):
        raise HTTPException(
            status_code=404,
            detail=error_response("EVENT_NOT_FOUND", "Event not found."),
        )
    if isinstance(exc, ReportAccessDeniedError):
        raise HTTPException(
            status_code=403,
            detail=error_response(
                "FORBIDDEN",
                "You are not assigned to this program.",
            ),
        )
    if isinstance(exc, InvalidReportDateRangeError):
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "INVALID_DATE_RANGE",
                "dateFrom must not be later than dateTo.",
                {"dateFrom": "Select a date on or before dateTo."},
            ),
        )
    raise exc


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    data = get_dashboard_summary(db, current_user)
    return success_response(data, "Dashboard summary retrieved.")


@router.get(
    "/reports/programs/{program_id}/summary",
    response_model=ProgramSummaryResponse,
)
def program_summary(
    program_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    date_from: Annotated[date | None, Query(alias="dateFrom")] = None,
    date_to: Annotated[date | None, Query(alias="dateTo")] = None,
) -> dict[str, Any]:
    try:
        data = get_program_summary(
            db,
            program_id,
            current_user,
            date_from=date_from,
            date_to=date_to,
        )
    except (
        InvalidReportDateRangeError,
        ReportAccessDeniedError,
        ReportProgramNotFoundError,
    ) as exc:
        _raise_report_error(exc)
    return success_response(data, "Program summary retrieved.")


@router.get(
    "/reports/events/{event_id}/attendance",
    response_model=EventAttendanceReportResponse,
)
def event_attendance_report(
    event_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        data = get_event_attendance_report(db, event_id, current_user)
    except (ReportAccessDeniedError, ReportEventNotFoundError) as exc:
        _raise_report_error(exc)
    return success_response(data, "Event attendance report retrieved.")
