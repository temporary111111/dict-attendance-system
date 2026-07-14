"""Admin routes para sa required/optional fixed attendance fields."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.models import User
from app.schemas.attendance_field_settings import (
    AttendanceFieldSettingsResponse,
    UpdateAttendanceFieldSettingsRequest,
)
from app.services.attendance_field_settings_service import (
    AttendanceFieldNotConfigurableError,
    FieldSettingsAccessDeniedError,
    FieldSettingsEventNotFoundError,
    FieldSettingsLockedError,
    InvalidFieldRequirementsError,
    UnknownAttendanceFieldError,
    get_event_attendance_field_settings,
    update_event_attendance_field_settings,
)

router = APIRouter(prefix="/events", tags=["attendance field settings"])


def _setting_data(setting) -> dict[str, Any]:
    return {
        "field_key": setting.field_key,
        "field_label": setting.field.field_label,
        "is_required": bool(setting.is_required),
        "is_admin_configurable": bool(setting.field.is_admin_configurable),
        "display_order": setting.field.display_order,
    }


def _raise_settings_error(exc: Exception) -> None:
    if isinstance(exc, FieldSettingsEventNotFoundError):
        raise HTTPException(
            status_code=404,
            detail=error_response("EVENT_NOT_FOUND", "Event not found."),
        )
    if isinstance(exc, FieldSettingsAccessDeniedError):
        raise HTTPException(
            status_code=403,
            detail=error_response(
                "FORBIDDEN",
                "You are not assigned to this program.",
            ),
        )
    if isinstance(exc, FieldSettingsLockedError):
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "FIELD_SETTINGS_LOCKED",
                "Field requirements cannot be changed for this event status.",
            ),
        )
    if isinstance(exc, UnknownAttendanceFieldError):
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "UNKNOWN_ATTENDANCE_FIELD",
                "One or more attendance fields are unknown.",
                {key: "Unknown attendance field." for key in exc.field_keys},
            ),
        )
    if isinstance(exc, AttendanceFieldNotConfigurableError):
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "FIELD_NOT_CONFIGURABLE",
                "Locked attendance fields cannot be changed.",
                {key: "This field is always required." for key in exc.field_keys},
            ),
        )
    if isinstance(exc, InvalidFieldRequirementsError):
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "INVALID_FIELD_REQUIREMENTS",
                "Street or postal requirements need a required PSGC address.",
                {"psgc_address": "Make PSGC address required first."},
            ),
        )
    raise exc


@router.get(
    "/{event_id}/attendance-field-settings",
    response_model=AttendanceFieldSettingsResponse,
)
def get_attendance_field_settings(
    event_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        settings = get_event_attendance_field_settings(db, event_id, current_user)
    except Exception as exc:
        _raise_settings_error(exc)
    return success_response(
        [_setting_data(setting) for setting in settings],
        "Attendance field settings retrieved.",
    )


@router.patch(
    "/{event_id}/attendance-field-settings",
    response_model=AttendanceFieldSettingsResponse,
)
def patch_attendance_field_settings(
    event_id: Annotated[int, Path(gt=0)],
    payload: UpdateAttendanceFieldSettingsRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    client_ip = request.client.host if request.client is not None else None
    try:
        settings = update_event_attendance_field_settings(
            db,
            event_id,
            payload,
            current_user,
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception as exc:
        _raise_settings_error(exc)
    return success_response(
        [_setting_data(setting) for setting in settings],
        "Attendance field settings updated.",
    )
