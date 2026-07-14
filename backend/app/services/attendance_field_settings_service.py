"""Access, validation, at audit rules para sa event field requirements."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event, ProgramAdminAssignment, User
from app.schemas.attendance_field_settings import (
    UpdateAttendanceFieldSettingsRequest,
)
from app.services.audit_service import build_audit_log


class FieldSettingsEventNotFoundError(Exception):
    """Raised kapag walang event para sa supplied ID."""


class FieldSettingsAccessDeniedError(Exception):
    """Raised kapag hindi assigned ang Program Admin sa event program."""


class FieldSettingsLockedError(Exception):
    """Raised kapag closed o archived na ang event."""


class UnknownAttendanceFieldError(Exception):
    def __init__(self, field_keys: list[str]):
        self.field_keys = field_keys


class AttendanceFieldNotConfigurableError(Exception):
    def __init__(self, field_keys: list[str]):
        self.field_keys = field_keys


class InvalidFieldRequirementsError(Exception):
    """Raised kapag conflicting ang PSGC at detailed address requirements."""


def _ensure_access(db: Session, event: Event, current_user: User) -> None:
    if current_user.role.role_name == "super_admin":
        return
    assignment_id = db.scalar(
        select(ProgramAdminAssignment.assignment_id).where(
            ProgramAdminAssignment.program_id == event.program_id,
            ProgramAdminAssignment.user_id == current_user.user_id,
            ProgramAdminAssignment.assignment_status == "active",
        )
    )
    if assignment_id is None:
        raise FieldSettingsAccessDeniedError


def _get_event(db: Session, event_id: int, current_user: User) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise FieldSettingsEventNotFoundError
    _ensure_access(db, event, current_user)
    return event


def _ordered_settings(event: Event):
    return sorted(
        event.attendance_field_settings,
        key=lambda setting: setting.field.display_order,
    )


def get_event_attendance_field_settings(
    db: Session,
    event_id: int,
    current_user: User,
):
    event = _get_event(db, event_id, current_user)
    return _ordered_settings(event)


def update_event_attendance_field_settings(
    db: Session,
    event_id: int,
    payload: UpdateAttendanceFieldSettingsRequest,
    current_user: User,
    *,
    ip_address: str | None,
    user_agent: str | None,
):
    event = _get_event(db, event_id, current_user)
    if event.event_status not in {"draft", "open"}:
        raise FieldSettingsLockedError

    settings_by_key = {
        setting.field_key: setting
        for setting in event.attendance_field_settings
    }
    unknown_keys = sorted(set(payload.requirements) - set(settings_by_key))
    if unknown_keys:
        raise UnknownAttendanceFieldError(unknown_keys)

    locked_keys = sorted(
        key
        for key in payload.requirements
        if not settings_by_key[key].field.is_admin_configurable
    )
    if locked_keys:
        raise AttendanceFieldNotConfigurableError(locked_keys)

    prospective = {
        key: bool(setting.is_required)
        for key, setting in settings_by_key.items()
    }
    prospective.update(payload.requirements)
    if (
        prospective.get("street_address")
        or prospective.get("postal_code")
    ) and not prospective.get("psgc_address"):
        raise InvalidFieldRequirementsError

    old_values = {
        key: bool(settings_by_key[key].is_required)
        for key, value in payload.requirements.items()
        if bool(settings_by_key[key].is_required) != value
    }
    if not old_values:
        return _ordered_settings(event)

    new_values = {key: payload.requirements[key] for key in old_values}
    for key, value in new_values.items():
        settings_by_key[key].is_required = value

    db.add(
        build_audit_log(
            user_id=current_user.user_id,
            action="updated_attendance_field_requirements",
            entity_type="event",
            entity_id=event.event_id,
            description="Updated required/optional attendance fields for event.",
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        for key, value in old_values.items():
            settings_by_key[key].is_required = value
        raise
    return _ordered_settings(event)
