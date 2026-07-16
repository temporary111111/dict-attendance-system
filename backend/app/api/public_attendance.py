"""Public event details at fixed attendance submission routes."""

from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Path,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.schemas.public_attendance import (
    AttendanceSubmissionRequest,
    AttendanceSubmissionResponse,
    PublicEventResponse,
)
from app.services.public_attendance_service import (
    AttendanceFieldValidationError,
    DuplicateAttendanceError,
    EventNotOpenError,
    InvalidPSGCAddressError,
    PublicEventNotFoundError,
    SignatureRequiredError,
    attendance_field_requirements,
    attendance_field_visibility,
    get_public_event,
    submit_attendance,
)
from app.services.signature_service import InvalidSignatureImageError

router = APIRouter(prefix="/public/events", tags=["public attendance"])


def _public_event_data(event) -> dict[str, Any]:
    return {
        "event_code": event.event_code,
        "event_title": event.event_title,
        "event_description": event.event_description,
        "venue": event.venue,
        "event_date": event.event_date,
        "event_status": event.event_status,
        "accepting_attendance": event.event_status == "open",
        "attendance_field_requirements": attendance_field_requirements(event),
        "attendance_field_visibility": attendance_field_visibility(event),
        "program": {
            "program_id": event.program.program_id,
            "program_name": event.program.program_name,
        },
    }


@router.get("/{event_code}", response_model=PublicEventResponse)
def get_public_event_record(
    event_code: Annotated[str, Path(min_length=1, max_length=100)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    try:
        event = get_public_event(db, event_code)
    except PublicEventNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "PUBLIC_EVENT_NOT_FOUND",
                "Public event was not found.",
            ),
        )
    return success_response(_public_event_data(event), "Public event retrieved.")


def _attendee_name(attendance) -> str:
    parts = [
        attendance.first_name,
        attendance.middle_name,
        attendance.last_name,
        attendance.suffix,
    ]
    return " ".join(part for part in parts if part)


@router.post(
    "/{event_code}/attendance",
    response_model=AttendanceSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_public_attendance(
    event_code: Annotated[str, Path(min_length=1, max_length=100)],
    payload: Annotated[
        AttendanceSubmissionRequest,
        Form(media_type="multipart/form-data"),
    ],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    try:
        result = submit_attendance(
            db,
            event_code,
            payload,
            payload.signature_image,
            request.app.state.settings,
        )
    except PublicEventNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "PUBLIC_EVENT_NOT_FOUND",
                "Public event was not found.",
            ),
        )
    except EventNotOpenError:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "EVENT_NOT_OPEN",
                "Attendance collection is not open for this event.",
            ),
        )
    except DuplicateAttendanceError:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "DUPLICATE_ATTENDANCE",
                "Attendance for this email has already been submitted for this event.",
            ),
        )
    except InvalidPSGCAddressError:
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "INVALID_PSGC_ADDRESS",
                "Select a valid and active PSGC address hierarchy.",
            ),
        )
    except AttendanceFieldValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "VALIDATION_ERROR",
                "Some fields are invalid.",
                exc.fields,
            ),
        )
    except SignatureRequiredError:
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "SIGNATURE_REQUIRED",
                "Type, draw, or upload your signature.",
            ),
        )
    except InvalidSignatureImageError:
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "INVALID_SIGNATURE_IMAGE",
                "Upload a valid PNG or JPEG signature image within the size limit.",
            ),
        )

    attendance = result.attendance
    return success_response(
        {
            "attendance_id": attendance.attendance_id,
            "event_code": result.event.event_code,
            "attendee_name": _attendee_name(attendance),
            "attendance_status": attendance.attendance_status,
            "submitted_at": attendance.submitted_at,
        },
        "Attendance submitted successfully.",
    )
