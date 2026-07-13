"""Role-aware admin routes para sa attendance record review."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.models import User
from app.schemas.attendance_records import (
    AttendanceRecordDetailResponse,
    AttendanceRecordListResponse,
    AttendanceStatus,
    UpdateAttendanceStatusRequest,
)
from app.services.attendance_record_service import (
    AttendanceEventNotFoundError,
    AttendanceRecordAccessDeniedError,
    AttendanceRecordNotFoundError,
    get_attendance_record,
    list_event_attendance_records,
    update_attendance_status,
)
from app.services.signature_service import resolve_signature_image

router = APIRouter(tags=["attendance records"])


def _attendee_name(attendance) -> str:
    parts = [
        attendance.first_name,
        attendance.middle_name,
        attendance.last_name,
        attendance.suffix,
    ]
    return " ".join(part for part in parts if part)


def _attendance_summary(attendance) -> dict[str, Any]:
    return {
        "attendance_id": attendance.attendance_id,
        "attendee_name": _attendee_name(attendance),
        "email": attendance.email,
        "affiliation": attendance.affiliation,
        "designation_category": attendance.designation_category,
        "sex": attendance.sex,
        "attendance_status": attendance.attendance_status,
        "duplicate_flag": attendance.duplicate_flag,
        "submitted_at": attendance.submitted_at,
    }


def _address_data(address) -> dict[str, Any] | None:
    if address is None:
        return None
    province = None
    if address.province is not None:
        province = {
            "code": address.province.province_code,
            "name": address.province.province_name,
        }
    return {
        "region": {
            "code": address.region.region_code,
            "name": address.region.region_name,
        },
        "province": province,
        "city_municipality": {
            "code": address.city_municipality.city_municipality_code,
            "name": address.city_municipality.city_municipality_name,
            "type": address.city_municipality.city_municipality_type,
        },
        "barangay": {
            "code": address.barangay.barangay_code,
            "name": address.barangay.barangay_name,
        },
        "street_address": address.street_address,
        "postal_code": address.postal_code,
    }


def _attendance_detail(attendance) -> dict[str, Any]:
    event = attendance.event
    return {
        "attendance_id": attendance.attendance_id,
        "first_name": attendance.first_name,
        "middle_name": attendance.middle_name,
        "last_name": attendance.last_name,
        "suffix": attendance.suffix,
        "email": attendance.email,
        "affiliation": attendance.affiliation,
        "designation_category": attendance.designation_category,
        "sex": attendance.sex,
        "consent_documentation_publication": (
            attendance.consent_documentation_publication
        ),
        "consent_database_processing": attendance.consent_database_processing,
        "attendance_status": attendance.attendance_status,
        "duplicate_flag": attendance.duplicate_flag,
        "submitted_at": attendance.submitted_at,
        "created_at": attendance.created_at,
        "updated_at": attendance.updated_at,
        "event": {
            "event_id": event.event_id,
            "event_title": event.event_title,
            "venue": event.venue,
            "event_date": event.event_date,
            "event_status": event.event_status,
            "program": {
                "program_id": event.program.program_id,
                "program_name": event.program.program_name,
            },
        },
        "address": _address_data(attendance.address),
        "signature": {
            "typed_name": attendance.signature_text,
            "has_image": attendance.signature_image_path is not None,
            "image_url": (
                f"/api/attendance-records/{attendance.attendance_id}/signature"
                if attendance.signature_image_path is not None
                else None
            ),
        },
    }


@router.get(
    "/events/{event_id}/attendance-records",
    response_model=AttendanceRecordListResponse,
)
def list_event_attendance(
    event_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 25,
    attendance_status: Annotated[
        AttendanceStatus | None,
        Query(alias="status"),
    ] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
) -> dict[str, Any]:
    normalized_search = search.strip() if search else None
    try:
        result = list_event_attendance_records(
            db,
            event_id,
            current_user,
            page=page,
            page_size=page_size,
            attendance_status=attendance_status,
            search=normalized_search,
        )
    except AttendanceEventNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=error_response("EVENT_NOT_FOUND", "Event not found."),
        )
    except AttendanceRecordAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail=error_response(
                "FORBIDDEN",
                "You are not assigned to this program.",
            ),
        )

    return success_response(
        {
            "items": [_attendance_summary(record) for record in result.items],
            "pagination": {
                "page": result.page,
                "page_size": result.page_size,
                "total_items": result.total_items,
                "total_pages": result.total_pages,
            },
        },
        "Attendance records retrieved.",
    )


@router.get(
    "/attendance-records/{attendance_id}/signature",
    response_class=FileResponse,
)
def get_attendance_signature(
    attendance_id: Annotated[int, Path(gt=0)],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        attendance = get_attendance_record(db, attendance_id, current_user)
    except AttendanceRecordNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "ATTENDANCE_RECORD_NOT_FOUND",
                "Attendance record not found.",
            ),
        )
    except AttendanceRecordAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail=error_response(
                "FORBIDDEN",
                "You are not assigned to this program.",
            ),
        )

    signature_path = resolve_signature_image(
        request.app.state.settings.signature_directory,
        attendance.signature_image_path,
    )
    if signature_path is None:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "SIGNATURE_IMAGE_NOT_FOUND",
                "Signature image not found.",
            ),
        )
    return FileResponse(
        signature_path,
        media_type="image/png",
        headers={"Cache-Control": "private, no-store"},
    )


@router.get(
    "/attendance-records/{attendance_id}",
    response_model=AttendanceRecordDetailResponse,
)
def get_attendance_record_detail(
    attendance_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        attendance = get_attendance_record(db, attendance_id, current_user)
    except AttendanceRecordNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "ATTENDANCE_RECORD_NOT_FOUND",
                "Attendance record not found.",
            ),
        )
    except AttendanceRecordAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail=error_response(
                "FORBIDDEN",
                "You are not assigned to this program.",
            ),
        )
    return success_response(
        _attendance_detail(attendance),
        "Attendance record retrieved.",
    )


@router.patch(
    "/attendance-records/{attendance_id}/status",
    response_model=AttendanceRecordDetailResponse,
)
def update_attendance_record_status(
    attendance_id: Annotated[int, Path(gt=0)],
    payload: UpdateAttendanceStatusRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    client_ip = request.client.host if request.client is not None else None
    try:
        attendance = update_attendance_status(
            db,
            attendance_id,
            payload,
            current_user,
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
        )
    except AttendanceRecordNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "ATTENDANCE_RECORD_NOT_FOUND",
                "Attendance record not found.",
            ),
        )
    except AttendanceRecordAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail=error_response(
                "FORBIDDEN",
                "You are not assigned to this program.",
            ),
        )
    return success_response(
        _attendance_detail(attendance),
        "Attendance status updated.",
    )
