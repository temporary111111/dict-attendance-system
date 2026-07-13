"""Queries at access rules para sa admin attendance record review."""

from dataclasses import dataclass
from math import ceil

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AttendanceRecord,
    AttendanceRecordAddress,
    Event,
    ProgramAdminAssignment,
    User,
)
from app.schemas.attendance_records import UpdateAttendanceStatusRequest
from app.services.audit_service import build_audit_log


class AttendanceEventNotFoundError(Exception):
    """Raised kapag walang event para sa attendance list."""


class AttendanceRecordAccessDeniedError(Exception):
    """Raised kapag hindi assigned ang Program Admin sa record program."""


class AttendanceRecordNotFoundError(Exception):
    """Raised kapag walang attendance record para sa supplied ID."""


@dataclass
class AttendanceRecordPage:
    items: list[AttendanceRecord]
    page: int
    page_size: int
    total_items: int
    total_pages: int


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
        raise AttendanceRecordAccessDeniedError


def list_event_attendance_records(
    db: Session,
    event_id: int,
    current_user: User,
    *,
    page: int,
    page_size: int,
    attendance_status: str | None,
    search: str | None,
) -> AttendanceRecordPage:
    event = db.get(Event, event_id)
    if event is None:
        raise AttendanceEventNotFoundError
    _ensure_program_access(db, event.program_id, current_user)

    filters = [AttendanceRecord.event_id == event_id]
    if attendance_status is not None:
        filters.append(AttendanceRecord.attendance_status == attendance_status)
    if search:
        pattern = f"%{search.lower()}%"
        full_name = func.lower(
            func.concat_ws(
                " ",
                AttendanceRecord.first_name,
                AttendanceRecord.middle_name,
                AttendanceRecord.last_name,
                AttendanceRecord.suffix,
            )
        )
        filters.append(
            or_(
                full_name.like(pattern),
                func.lower(AttendanceRecord.email).like(pattern),
                func.lower(AttendanceRecord.affiliation).like(pattern),
                func.lower(AttendanceRecord.designation_category).like(pattern),
            )
        )

    total_items = db.scalar(
        select(func.count(AttendanceRecord.attendance_id)).where(*filters)
    ) or 0
    records = list(
        db.scalars(
            select(AttendanceRecord)
            .where(*filters)
            .order_by(
                AttendanceRecord.submitted_at.desc(),
                AttendanceRecord.attendance_id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return AttendanceRecordPage(
        items=records,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=ceil(total_items / page_size) if total_items else 0,
    )


def get_attendance_record(
    db: Session,
    attendance_id: int,
    current_user: User,
) -> AttendanceRecord:
    record = db.scalar(
        select(AttendanceRecord)
        .options(
            selectinload(AttendanceRecord.event).selectinload(Event.program),
            selectinload(AttendanceRecord.address).selectinload(
                AttendanceRecordAddress.region
            ),
            selectinload(AttendanceRecord.address).selectinload(
                AttendanceRecordAddress.province
            ),
            selectinload(AttendanceRecord.address).selectinload(
                AttendanceRecordAddress.city_municipality
            ),
            selectinload(AttendanceRecord.address).selectinload(
                AttendanceRecordAddress.barangay
            ),
        )
        .where(AttendanceRecord.attendance_id == attendance_id)
    )
    if record is None:
        raise AttendanceRecordNotFoundError
    _ensure_program_access(db, record.event.program_id, current_user)
    return record


def update_attendance_status(
    db: Session,
    attendance_id: int,
    payload: UpdateAttendanceStatusRequest,
    current_user: User,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> AttendanceRecord:
    attendance = get_attendance_record(db, attendance_id, current_user)
    old_status = attendance.attendance_status
    if old_status == payload.attendance_status:
        return attendance

    attendance.attendance_status = payload.attendance_status
    audit_log = build_audit_log(
        user_id=current_user.user_id,
        action="attendance_status_changed",
        entity_type="attendance_record",
        entity_id=attendance.attendance_id,
        description=(
            f"Attendance status changed from {old_status} to "
            f"{payload.attendance_status}. Reason: {payload.reason}"
        ),
        old_values={"attendance_status": old_status},
        new_values={
            "attendance_status": payload.attendance_status,
            "reason": payload.reason,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    try:
        db.commit()
    except Exception:
        db.rollback()
        attendance.attendance_status = old_status
        raise
    db.refresh(attendance)
    return attendance
