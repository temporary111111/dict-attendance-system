"""Access, query, at audit transaction para sa attendance-sheet export."""

import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AttendanceRecord,
    AttendanceSheetExport,
    Event,
    Program,
    ProgramAdminAssignment,
    User,
)
from app.services.attendance_sheet_pdf import (
    AttendanceSheetEvent,
    AttendanceSheetPDFError,
    AttendanceSheetRow,
    render_attendance_sheet_pdf,
)
from app.services.audit_service import build_audit_log
from app.services.signature_service import resolve_signature_image


class AttendanceSheetEventNotFoundError(Exception):
    """Raised kapag walang selected event."""


class AttendanceSheetAccessDeniedError(Exception):
    """Raised kapag hindi assigned ang Program Admin sa event program."""


class AttendanceSheetGenerationError(Exception):
    """Raised kapag hindi mabuo ang PDF bytes."""


class AttendanceSheetExportPersistenceError(Exception):
    """Raised kapag hindi ma-save nang buo ang export at audit history."""


@dataclass
class AttendanceSheetExportResult:
    pdf_bytes: bytes
    filename: str
    export: AttendanceSheetExport


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
        raise AttendanceSheetAccessDeniedError


def _attendee_name(record: AttendanceRecord) -> str:
    return " ".join(
        part
        for part in (
            record.first_name,
            record.middle_name,
            record.last_name,
            record.suffix,
        )
        if part
    )


def _safe_filename(event: Event) -> str:
    safe_code = re.sub(r"[^A-Za-z0-9._-]+", "-", event.event_code)
    safe_code = safe_code.strip(".-_") or f"event-{event.event_id}"
    return f"attendance-sheet-{safe_code}.pdf"


def generate_attendance_sheet_export(
    db: Session,
    event_id: int,
    current_user: User,
    *,
    logo_path: Path,
    signature_directory: Path,
    ip_address: str | None,
    user_agent: str | None,
) -> AttendanceSheetExportResult:
    """Gumagawa ng current event PDF at sabay sine-save ang export history."""
    event = db.scalar(
        select(Event)
        .options(
            selectinload(Event.program).selectinload(Program.owning_unit),
        )
        .where(Event.event_id == event_id)
    )
    if event is None:
        raise AttendanceSheetEventNotFoundError
    _ensure_program_access(db, event.program_id, current_user)

    records = list(
        db.scalars(
            select(AttendanceRecord)
            .where(
                AttendanceRecord.event_id == event_id,
                AttendanceRecord.attendance_status == "valid",
            )
            .order_by(
                AttendanceRecord.submitted_at.asc(),
                AttendanceRecord.attendance_id.asc(),
            )
        ).all()
    )
    event_data = AttendanceSheetEvent(
        office_name=event.program.owning_unit.unit_name,
        event_title=event.event_title,
        venue=event.venue,
        event_date=event.event_date,
    )
    rows = [
        AttendanceSheetRow(
            row_number=index,
            attendee_name=_attendee_name(record),
            affiliation=record.affiliation,
            designation_category=record.designation_category,
            sex=record.sex,
            email=record.email,
            consent_documentation_publication=(
                record.consent_documentation_publication
            ),
            consent_database_processing=record.consent_database_processing,
            signature_text=record.signature_text,
            signature_image_path=resolve_signature_image(
                signature_directory,
                record.signature_image_path,
            ),
        )
        for index, record in enumerate(records, start=1)
    ]
    try:
        pdf_bytes = render_attendance_sheet_pdf(
            event_data,
            rows,
            logo_path=logo_path,
        )
    except AttendanceSheetPDFError as exc:
        raise AttendanceSheetGenerationError from exc

    export = AttendanceSheetExport(
        event_id=event.event_id,
        exported_by_user_id=current_user.user_id,
        export_format="pdf",
        file_path=None,
        total_records=len(records),
    )
    try:
        db.add(export)
        # Kailangan muna ang export ID para maituro rito ang audit entry.
        db.flush()
        db.add(
            build_audit_log(
                user_id=current_user.user_id,
                action="generated_attendance_sheet",
                entity_type="attendance_sheet_export",
                entity_id=export.export_id,
                description=(
                    f"Generated PDF attendance sheet for event "
                    f"{event.event_id} with {len(records)} valid records."
                ),
                old_values=None,
                new_values={
                    "event_id": event.event_id,
                    "export_format": "pdf",
                    "total_records": len(records),
                    "event_status": event.event_status,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise AttendanceSheetExportPersistenceError from exc

    return AttendanceSheetExportResult(
        pdf_bytes=pdf_bytes,
        filename=_safe_filename(event),
        export=export,
    )
