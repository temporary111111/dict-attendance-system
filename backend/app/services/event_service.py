"""Business rules para sa event access, QR link, at status lifecycle."""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models import Event, Program, ProgramAdminAssignment, User
from app.schemas.events import CreateEventRequest, UpdateEventRequest
from app.services.qr_code_service import (
    QRCodeGenerationError,
    generate_qr_png,
    remove_qr_png,
)


class EventNotFoundError(Exception):
    """Raised kapag walang event para sa supplied ID."""


class EventAccessDeniedError(Exception):
    """Raised kapag hindi assigned ang Program Admin sa event program."""


class EventProgramNotFoundError(Exception):
    """Raised kapag walang target program sa event creation."""


class EventProgramArchivedError(Exception):
    """Raised kapag archived ang target program."""


class EventArchivedError(Exception):
    """Raised kapag may write action sa archived event."""


class EventCodeGenerationError(Exception):
    """Raised kapag hindi makagawa ng unique public event code."""


class AttendanceLinkRequiredError(Exception):
    """Raised kapag io-open ang event na wala pang link at QR."""


class InvalidEventTransitionError(Exception):
    """Raised kapag invalid ang requested event status transition."""


class EventMustBeClosedError(Exception):
    """Raised kapag ina-archive ang currently open event."""


@dataclass
class EventResult:
    event: Event
    program: Program


def _now_without_timezone() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _commit_event_write(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EventCodeGenerationError from exc


def _generate_unique_event_code(db: Session) -> str:
    for _ in range(5):
        event_code = secrets.token_urlsafe(24)
        existing_event_id = db.scalar(
            select(Event.event_id).where(Event.event_code == event_code)
        )
        if existing_event_id is None:
            return event_code
    raise EventCodeGenerationError


def _ensure_program_access(
    db: Session,
    program_id: int,
    current_user: User,
) -> None:
    if current_user.role.role_name == "super_admin":
        return
    assignment_id = db.scalar(
        select(ProgramAdminAssignment.assignment_id).where(
            ProgramAdminAssignment.program_id == program_id,
            ProgramAdminAssignment.user_id == current_user.user_id,
            ProgramAdminAssignment.assignment_status == "active",
        )
    )
    if assignment_id is None:
        raise EventAccessDeniedError


def _get_accessible_event(
    db: Session,
    event_id: int,
    current_user: User,
) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise EventNotFoundError
    _ensure_program_access(db, event.program_id, current_user)
    return event


def _ensure_event_is_writable(
    event: Event,
    *,
    require_active_program: bool = True,
) -> None:
    if event.event_status == "archived":
        raise EventArchivedError
    if require_active_program and event.program.program_status != "active":
        raise EventProgramArchivedError


def list_visible_events(db: Session, current_user: User) -> list[Event]:
    statement = (
        select(Event)
        .options(selectinload(Event.program))
        .where(Event.event_status != "archived")
    )
    if current_user.role.role_name == "program_admin":
        statement = statement.join(
            ProgramAdminAssignment,
            ProgramAdminAssignment.program_id == Event.program_id,
        ).where(
            ProgramAdminAssignment.user_id == current_user.user_id,
            ProgramAdminAssignment.assignment_status == "active",
        )
    statement = statement.order_by(Event.event_date.desc(), Event.event_title)
    return list(db.scalars(statement).all())


def create_event(
    db: Session,
    program_id: int,
    payload: CreateEventRequest,
    current_user: User,
) -> EventResult:
    program = db.get(Program, program_id)
    if program is None:
        raise EventProgramNotFoundError
    _ensure_program_access(db, program_id, current_user)
    if program.program_status != "active":
        raise EventProgramArchivedError

    event = Event(
        program_id=program_id,
        created_by_user_id=current_user.user_id,
        event_title=payload.event_title,
        event_description=payload.event_description,
        venue=payload.venue,
        event_date=payload.event_date,
        event_code=_generate_unique_event_code(db),
        public_attendance_url=None,
        qr_code_path=None,
        event_status="draft",
        opened_at=None,
        closed_at=None,
    )
    db.add(event)
    _commit_event_write(db)
    db.refresh(event)
    return EventResult(event=event, program=program)


def get_event(
    db: Session,
    event_id: int,
    current_user: User,
) -> Event:
    return _get_accessible_event(db, event_id, current_user)


def update_event(
    db: Session,
    event_id: int,
    payload: UpdateEventRequest,
    current_user: User,
) -> Event:
    event = _get_accessible_event(db, event_id, current_user)
    _ensure_event_is_writable(event)
    supplied_fields = payload.model_fields_set

    if "event_title" in supplied_fields:
        event.event_title = payload.event_title
    if "event_description" in supplied_fields:
        event.event_description = payload.event_description
    if "venue" in supplied_fields:
        event.venue = payload.venue
    if "event_date" in supplied_fields:
        event.event_date = payload.event_date

    _commit_event_write(db)
    db.refresh(event)
    return event


def refresh_attendance_link(
    db: Session,
    event_id: int,
    current_user: User,
    settings: Settings,
) -> Event:
    event = _get_accessible_event(db, event_id, current_user)
    _ensure_event_is_writable(event)
    old_qr_path = event.qr_code_path
    event_code = _generate_unique_event_code(db)
    attendance_url = settings.public_attendance_url_template.format(
        event_code=event_code
    )
    filename = f"event-{event.event_id}-{event_code}.png"
    public_qr_path = f"{settings.qr_code_url_prefix}/{filename}"

    generate_qr_png(attendance_url, settings.qr_code_directory, filename)
    event.event_code = event_code
    event.public_attendance_url = attendance_url
    event.qr_code_path = public_qr_path
    try:
        _commit_event_write(db)
    except EventCodeGenerationError:
        remove_qr_png(settings.qr_code_directory, public_qr_path)
        raise

    db.refresh(event)
    if old_qr_path != public_qr_path:
        remove_qr_png(settings.qr_code_directory, old_qr_path)
    return event


def open_event(db: Session, event_id: int, current_user: User) -> Event:
    event = _get_accessible_event(db, event_id, current_user)
    _ensure_event_is_writable(event)
    if event.event_status == "open":
        return event
    if not event.public_attendance_url or not event.qr_code_path:
        raise AttendanceLinkRequiredError

    event.event_status = "open"
    event.opened_at = _now_without_timezone()
    event.closed_at = None
    _commit_event_write(db)
    db.refresh(event)
    return event


def close_event(db: Session, event_id: int, current_user: User) -> Event:
    event = _get_accessible_event(db, event_id, current_user)
    # Closing stays allowed para ma-resolve kahit legacy archived ang parent.
    _ensure_event_is_writable(event, require_active_program=False)
    if event.event_status == "closed":
        return event
    if event.event_status != "open":
        raise InvalidEventTransitionError

    event.event_status = "closed"
    event.closed_at = _now_without_timezone()
    _commit_event_write(db)
    db.refresh(event)
    return event


def archive_event(db: Session, event_id: int) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise EventNotFoundError
    if event.event_status == "archived":
        return event
    if event.event_status == "open":
        raise EventMustBeClosedError

    event.event_status = "archived"
    _commit_event_write(db)
    db.refresh(event)
    return event
