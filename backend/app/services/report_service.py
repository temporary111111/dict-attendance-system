"""Role-scoped aggregate queries para sa dashboard at reports."""

from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AttendanceRecord,
    Event,
    Program,
    ProgramAdminAssignment,
    User,
)

ATTENDANCE_STATUSES = ("valid", "duplicate", "invalid", "void")
EVENT_STATUSES = ("draft", "open", "closed", "archived")


class ReportProgramNotFoundError(Exception):
    """Raised kapag walang selected program."""


class ReportEventNotFoundError(Exception):
    """Raised kapag walang selected event."""


class ReportAccessDeniedError(Exception):
    """Raised kapag hindi assigned ang Program Admin sa selected program."""


class InvalidReportDateRangeError(Exception):
    """Raised kapag mas huli ang date_from kaysa date_to."""


def _empty_counts(keys: tuple[str, ...]) -> dict[str, int]:
    return {key: 0 for key in keys}


def _active_assigned_program_ids(current_user: User):
    return select(ProgramAdminAssignment.program_id).where(
        ProgramAdminAssignment.user_id == current_user.user_id,
        ProgramAdminAssignment.assignment_status == "active",
    )


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
        raise ReportAccessDeniedError


def _status_counts(db: Session, statement, statuses: tuple[str, ...]):
    counts = _empty_counts(statuses)
    for status, total in db.execute(statement).all():
        counts[status] = int(total)
    return counts


def get_dashboard_summary(db: Session, current_user: User) -> dict:
    program_filters = [Program.program_status == "active"]
    if current_user.role.role_name == "program_admin":
        program_filters.append(
            Program.program_id.in_(_active_assigned_program_ids(current_user))
        )
    visible_program_ids = select(Program.program_id).where(*program_filters)
    event_filters = [
        Event.program_id.in_(visible_program_ids),
        Event.event_status != "archived",
    ]

    program_total = db.scalar(
        select(func.count(Program.program_id)).where(*program_filters)
    ) or 0
    event_total = db.scalar(
        select(func.count(Event.event_id)).where(*event_filters)
    ) or 0
    attendance_total = db.scalar(
        select(func.count(AttendanceRecord.attendance_id))
        .join(Event, Event.event_id == AttendanceRecord.event_id)
        .where(*event_filters)
    ) or 0

    events_by_status = _status_counts(
        db,
        select(Event.event_status, func.count(Event.event_id))
        .where(*event_filters)
        .group_by(Event.event_status),
        EVENT_STATUSES,
    )
    attendance_by_status = _status_counts(
        db,
        select(
            AttendanceRecord.attendance_status,
            func.count(AttendanceRecord.attendance_id),
        )
        .join(Event, Event.event_id == AttendanceRecord.event_id)
        .where(*event_filters)
        .group_by(AttendanceRecord.attendance_status),
        ATTENDANCE_STATUSES,
    )

    valid_count = func.sum(
        case((AttendanceRecord.attendance_status == "valid", 1), else_=0)
    )
    recent_rows = db.execute(
        select(
            Event.event_id,
            Event.program_id,
            Program.program_name,
            Event.event_title,
            Event.event_date,
            Event.event_status,
            func.count(AttendanceRecord.attendance_id).label("total_attendance"),
            func.coalesce(valid_count, 0).label("valid_attendance"),
        )
        .join(Program, Program.program_id == Event.program_id)
        .outerjoin(
            AttendanceRecord,
            AttendanceRecord.event_id == Event.event_id,
        )
        .where(*event_filters)
        .group_by(
            Event.event_id,
            Event.program_id,
            Program.program_name,
            Event.event_title,
            Event.event_date,
            Event.event_status,
        )
        .order_by(Event.event_date.desc(), Event.event_id.desc())
        .limit(5)
    ).all()

    return {
        "totals": {
            "programs": int(program_total),
            "events": int(event_total),
            "attendance_records": int(attendance_total),
        },
        "events_by_status": events_by_status,
        "attendance_by_status": attendance_by_status,
        "recent_events": [
            {
                "event_id": row.event_id,
                "program_id": row.program_id,
                "program_name": row.program_name,
                "event_title": row.event_title,
                "event_date": row.event_date,
                "event_status": row.event_status,
                "total_attendance": int(row.total_attendance),
                "valid_attendance": int(row.valid_attendance),
            }
            for row in recent_rows
        ],
    }


def get_program_summary(
    db: Session,
    program_id: int,
    current_user: User,
    *,
    date_from: date | None,
    date_to: date | None,
) -> dict:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise InvalidReportDateRangeError
    program = db.get(Program, program_id)
    if program is None:
        raise ReportProgramNotFoundError
    _ensure_program_access(db, program_id, current_user)

    event_filters = [Event.program_id == program_id]
    if date_from is not None:
        event_filters.append(Event.event_date >= date_from)
    if date_to is not None:
        event_filters.append(Event.event_date <= date_to)

    valid_count = func.sum(
        case((AttendanceRecord.attendance_status == "valid", 1), else_=0)
    )
    event_rows = db.execute(
        select(
            Event.event_id,
            Event.event_title,
            Event.event_date,
            Event.event_status,
            func.count(AttendanceRecord.attendance_id).label("total_attendance"),
            func.coalesce(valid_count, 0).label("valid_attendance"),
        )
        .outerjoin(
            AttendanceRecord,
            AttendanceRecord.event_id == Event.event_id,
        )
        .where(*event_filters)
        .group_by(
            Event.event_id,
            Event.event_title,
            Event.event_date,
            Event.event_status,
        )
        .order_by(Event.event_date.desc(), Event.event_id.desc())
    ).all()

    event_ids = select(Event.event_id).where(*event_filters)
    attendance_by_status = _status_counts(
        db,
        select(
            AttendanceRecord.attendance_status,
            func.count(AttendanceRecord.attendance_id),
        )
        .where(AttendanceRecord.event_id.in_(event_ids))
        .group_by(AttendanceRecord.attendance_status),
        ATTENDANCE_STATUSES,
    )
    events_by_status = _empty_counts(EVENT_STATUSES)
    for row in event_rows:
        events_by_status[row.event_status] += 1

    event_dates = [row.event_date for row in event_rows]
    return {
        "program_id": program.program_id,
        "program_name": program.program_name,
        "program_status": program.program_status,
        "date_range": {
            "date_from": date_from or (min(event_dates) if event_dates else None),
            "date_to": date_to or (max(event_dates) if event_dates else None),
        },
        "total_events": len(event_rows),
        "total_attendance": sum(attendance_by_status.values()),
        "events_by_status": events_by_status,
        "attendance_by_status": attendance_by_status,
        "events": [
            {
                "event_id": row.event_id,
                "event_title": row.event_title,
                "event_date": row.event_date,
                "event_status": row.event_status,
                "total_attendance": int(row.total_attendance),
                "valid_attendance": int(row.valid_attendance),
            }
            for row in event_rows
        ],
    }


def get_event_attendance_report(
    db: Session,
    event_id: int,
    current_user: User,
) -> dict:
    event = db.scalar(
        select(Event)
        .options(selectinload(Event.program))
        .where(Event.event_id == event_id)
    )
    if event is None:
        raise ReportEventNotFoundError
    _ensure_program_access(db, event.program_id, current_user)

    attendance_by_status = _status_counts(
        db,
        select(
            AttendanceRecord.attendance_status,
            func.count(AttendanceRecord.attendance_id),
        )
        .where(AttendanceRecord.event_id == event_id)
        .group_by(AttendanceRecord.attendance_status),
        ATTENDANCE_STATUSES,
    )
    sex_rows = db.execute(
        select(AttendanceRecord.sex, func.count(AttendanceRecord.attendance_id))
        .where(AttendanceRecord.event_id == event_id)
        .group_by(AttendanceRecord.sex)
    ).all()
    sex_counts = {"female": 0, "male": 0, "unspecified": 0}
    for sex, total in sex_rows:
        key = "female" if sex == "F" else "male" if sex == "M" else "unspecified"
        sex_counts[key] += int(total)

    consent_rows = db.execute(
        select(
            AttendanceRecord.consent_documentation_publication,
            func.count(AttendanceRecord.attendance_id),
        )
        .where(AttendanceRecord.event_id == event_id)
        .group_by(AttendanceRecord.consent_documentation_publication)
    ).all()
    consent_counts = {"accepted": 0, "declined": 0}
    for accepted, total in consent_rows:
        consent_counts["accepted" if accepted else "declined"] += int(total)

    return {
        "event_id": event.event_id,
        "event_title": event.event_title,
        "event_date": event.event_date,
        "venue": event.venue,
        "event_status": event.event_status,
        "program_id": event.program.program_id,
        "program_name": event.program.program_name,
        "total_attendance": sum(attendance_by_status.values()),
        "attendance_by_status": attendance_by_status,
        "attendees_by_sex": sex_counts,
        "documentation_consent": consent_counts,
    }
