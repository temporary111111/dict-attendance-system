"""Role-aware event management, QR link, at lifecycle routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_super_admin
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.models import Event, Program, User
from app.schemas.events import (
    CreateEventRequest,
    EventListResponse,
    EventResponse,
    UpdateEventRequest,
)
from app.services.event_service import (
    AttendanceLinkRequiredError,
    EventAccessDeniedError,
    EventArchivedError,
    EventCodeGenerationError,
    EventMustBeClosedError,
    EventNotFoundError,
    EventProgramArchivedError,
    EventProgramNotFoundError,
    InvalidEventTransitionError,
    archive_event,
    close_event,
    create_event,
    get_event,
    list_visible_events,
    open_event,
    refresh_attendance_link,
    update_event,
)
from app.services.qr_code_service import QRCodeGenerationError

router = APIRouter(tags=["events"])


def _event_data(event: Event, program: Program | None = None) -> dict[str, Any]:
    event_program = program or event.program
    return {
        "event_id": event.event_id,
        "program": {
            "program_id": event_program.program_id,
            "program_name": event_program.program_name,
        },
        "created_by_user_id": event.created_by_user_id,
        "event_title": event.event_title,
        "event_description": event.event_description,
        "venue": event.venue,
        "event_date": event.event_date,
        "event_code": event.event_code,
        "public_attendance_url": event.public_attendance_url,
        "qr_code_path": event.qr_code_path,
        "event_status": event.event_status,
        "opened_at": event.opened_at,
        "closed_at": event.closed_at,
    }


def _raise_event_error(exc: Exception) -> None:
    if isinstance(exc, (EventNotFoundError, EventProgramNotFoundError)):
        code = "EVENT_NOT_FOUND" if isinstance(exc, EventNotFoundError) else "PROGRAM_NOT_FOUND"
        message = "Event not found." if code == "EVENT_NOT_FOUND" else "Program not found."
        raise HTTPException(status_code=404, detail=error_response(code, message))
    if isinstance(exc, EventAccessDeniedError):
        raise HTTPException(
            status_code=403,
            detail=error_response("FORBIDDEN", "You are not assigned to this program."),
        )
    if isinstance(exc, EventProgramArchivedError):
        raise HTTPException(
            status_code=409,
            detail=error_response("PROGRAM_ARCHIVED", "Archived programs cannot accept new events."),
        )
    if isinstance(exc, EventArchivedError):
        raise HTTPException(
            status_code=409,
            detail=error_response("EVENT_ARCHIVED", "Archived events cannot be changed."),
        )
    if isinstance(exc, AttendanceLinkRequiredError):
        raise HTTPException(
            status_code=409,
            detail=error_response("ATTENDANCE_LINK_REQUIRED", "Generate the attendance link and QR code first."),
        )
    if isinstance(exc, InvalidEventTransitionError):
        raise HTTPException(
            status_code=409,
            detail=error_response("INVALID_EVENT_TRANSITION", "The event cannot move to the requested status."),
        )
    if isinstance(exc, EventMustBeClosedError):
        raise HTTPException(
            status_code=409,
            detail=error_response("EVENT_MUST_BE_CLOSED", "Close the event before archiving it."),
        )
    if isinstance(exc, (EventCodeGenerationError, QRCodeGenerationError)):
        raise HTTPException(
            status_code=500,
            detail=error_response("QR_CODE_GENERATION_FAILED", "The attendance link and QR code could not be generated."),
        )


@router.get("/events", response_model=EventListResponse)
def list_events(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    events = list_visible_events(db, current_user)
    return success_response([_event_data(event) for event in events], "Events retrieved.")


@router.post(
    "/programs/{program_id}/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event_record(
    program_id: Annotated[int, Path(gt=0)],
    payload: CreateEventRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        created = create_event(db, program_id, payload, current_user)
    except (
        EventAccessDeniedError,
        EventCodeGenerationError,
        EventProgramArchivedError,
        EventProgramNotFoundError,
    ) as exc:
        _raise_event_error(exc)
    return success_response(_event_data(created.event, created.program), "Event created.")


@router.get("/events/{event_id}", response_model=EventResponse)
def get_event_record(
    event_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        event = get_event(db, event_id, current_user)
    except (EventAccessDeniedError, EventNotFoundError) as exc:
        _raise_event_error(exc)
    return success_response(_event_data(event), "Event retrieved.")


@router.patch("/events/{event_id}", response_model=EventResponse)
def update_event_record(
    event_id: Annotated[int, Path(gt=0)],
    payload: UpdateEventRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        event = update_event(db, event_id, payload, current_user)
    except (
        EventAccessDeniedError,
        EventArchivedError,
        EventNotFoundError,
        EventProgramArchivedError,
    ) as exc:
        _raise_event_error(exc)
    return success_response(_event_data(event), "Event updated.")


@router.post("/events/{event_id}/attendance-link", response_model=EventResponse)
def refresh_event_attendance_link(
    event_id: Annotated[int, Path(gt=0)],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        event = refresh_attendance_link(
            db,
            event_id,
            current_user,
            request.app.state.settings,
        )
    except (
        EventAccessDeniedError,
        EventArchivedError,
        EventCodeGenerationError,
        EventNotFoundError,
        EventProgramArchivedError,
        QRCodeGenerationError,
    ) as exc:
        _raise_event_error(exc)
    return success_response(_event_data(event), "Attendance link and QR code generated.")


@router.post("/events/{event_id}/open", response_model=EventResponse)
def open_event_record(
    event_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        event = open_event(db, event_id, current_user)
    except (
        AttendanceLinkRequiredError,
        EventAccessDeniedError,
        EventArchivedError,
        EventNotFoundError,
        EventProgramArchivedError,
    ) as exc:
        _raise_event_error(exc)
    return success_response(_event_data(event), "Event attendance opened.")


@router.post("/events/{event_id}/close", response_model=EventResponse)
def close_event_record(
    event_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        event = close_event(db, event_id, current_user)
    except (
        EventAccessDeniedError,
        EventArchivedError,
        EventNotFoundError,
        InvalidEventTransitionError,
    ) as exc:
        _raise_event_error(exc)
    return success_response(_event_data(event), "Event attendance closed.")


@router.patch("/events/{event_id}/archive", response_model=EventResponse)
def archive_event_record(
    event_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_super_admin: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        event = archive_event(db, event_id)
    except (EventMustBeClosedError, EventNotFoundError) as exc:
        _raise_event_error(exc)
    return success_response(_event_data(event), "Event archived.")
