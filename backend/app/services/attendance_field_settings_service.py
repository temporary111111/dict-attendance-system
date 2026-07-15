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
    requested_requirements = payload.requirements or {}
    requested_visibility = payload.visibility or {}
    requested_keys = set(requested_requirements) | set(requested_visibility)
    unknown_keys = sorted(requested_keys - set(settings_by_key))
    if unknown_keys:
        raise UnknownAttendanceFieldError(unknown_keys)

    locked_keys = sorted(
        key
        for key in requested_keys
        if not settings_by_key[key].field.is_admin_configurable
    )
    if locked_keys:
        raise AttendanceFieldNotConfigurableError(locked_keys)

    prospective_requirements = {
        key: bool(setting.is_required)
        for key, setting in settings_by_key.items()
    }
    prospective_visibility = {
        key: bool(getattr(setting, "is_visible", True))
        for key, setting in settings_by_key.items()
    }
    prospective_requirements.update(requested_requirements)
    prospective_visibility.update(requested_visibility)

    for key, is_visible in requested_visibility.items():
        if not is_visible:
            prospective_requirements[key] = False
    if not prospective_visibility["psgc_address"]:
        for key in ("street_address", "postal_code"):
            prospective_visibility[key] = False
            prospective_requirements[key] = False

    if (
        prospective_requirements["street_address"]
        or prospective_requirements["postal_code"]
    ) and not prospective_requirements["psgc_address"]:
        raise InvalidFieldRequirementsError
    if any(
        prospective_requirements[key] and not prospective_visibility[key]
        for key in settings_by_key
    ):
        raise InvalidFieldRequirementsError
    if (
        prospective_visibility["street_address"]
        or prospective_visibility["postal_code"]
    ) and not prospective_visibility["psgc_address"]:
        raise InvalidFieldRequirementsError

    old_requirements = {
        key: bool(settings_by_key[key].is_required)
        for key, value in prospective_requirements.items()
        if bool(settings_by_key[key].is_required) != value
    }
    old_visibility = {
        key: bool(getattr(settings_by_key[key], "is_visible", True))
        for key, value in prospective_visibility.items()
        if bool(settings_by_key[key].is_visible) != value
    }
    if not old_requirements and not old_visibility:
        return _ordered_settings(event)

    new_requirements = {
        key: prospective_requirements[key] for key in old_requirements
    }
    new_visibility = {
        key: prospective_visibility[key] for key in old_visibility
    }
    for key, value in new_requirements.items():
        settings_by_key[key].is_required = value
    for key, value in new_visibility.items():
        settings_by_key[key].is_visible = value

    if old_visibility:
        old_values = {
            "requirements": old_requirements,
            "visibility": old_visibility,
        }
        new_values = {
            "requirements": new_requirements,
            "visibility": new_visibility,
        }
    else:
        old_values = old_requirements
        new_values = new_requirements

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
        for key, value in old_requirements.items():
            settings_by_key[key].is_required = value
        for key, value in old_visibility.items():
            settings_by_key[key].is_visible = value
        raise
    return _ordered_settings(event)
