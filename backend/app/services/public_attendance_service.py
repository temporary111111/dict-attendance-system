"""Public event lookup at transactional attendance submission rules."""

from dataclasses import dataclass

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models import (
    AttendanceRecord,
    AttendanceRecordAddress,
    Event,
    PSGCBarangay,
    PSGCCityMunicipality,
    PSGCProvince,
    PSGCRegion,
)
from app.schemas.public_attendance import AttendanceSubmissionRequest
from app.services.signature_service import (
    remove_signature_image,
    save_signature_image,
)


class PublicEventNotFoundError(Exception):
    """Raised kapag invalid, rotated, o archived ang public event code."""


class EventNotOpenError(Exception):
    """Raised kapag hindi open ang attendance collection."""


class DuplicateAttendanceError(Exception):
    """Raised kapag may attendance na ang email sa same event."""


class InvalidPSGCAddressError(Exception):
    """Raised kapag inactive, missing, o mismatched ang PSGC hierarchy."""


class SignatureRequiredError(Exception):
    """Raised kapag walang typed o uploaded signature."""


@dataclass
class AttendanceSubmissionResult:
    attendance: AttendanceRecord
    event: Event


def _is_duplicate_entry_error(error: IntegrityError) -> bool:
    error_args = getattr(error.orig, "args", ())
    return bool(error_args) and error_args[0] == 1062


def get_public_event(db: Session, event_code: str) -> Event:
    event = db.scalar(
        select(Event)
        .options(selectinload(Event.program))
        .where(
            Event.event_code == event_code,
            Event.event_status != "archived",
        )
    )
    if event is None:
        raise PublicEventNotFoundError
    return event


def _validate_psgc_address(
    db: Session,
    payload: AttendanceSubmissionRequest,
) -> None:
    if not payload.has_address:
        return

    region = db.get(PSGCRegion, payload.region_code)
    province = (
        db.get(PSGCProvince, payload.province_code)
        if payload.province_code is not None
        else None
    )
    city = db.get(PSGCCityMunicipality, payload.city_municipality_code)
    barangay = db.get(PSGCBarangay, payload.barangay_code)

    if region is None or not region.is_active:
        raise InvalidPSGCAddressError
    if city is None or not city.is_active or city.region_code != region.region_code:
        raise InvalidPSGCAddressError
    if barangay is None or not barangay.is_active:
        raise InvalidPSGCAddressError
    if barangay.city_municipality_code != city.city_municipality_code:
        raise InvalidPSGCAddressError

    if payload.province_code is None:
        if city.province_code is not None:
            raise InvalidPSGCAddressError
    elif (
        province is None
        or not province.is_active
        or province.region_code != region.region_code
        or city.province_code != province.province_code
    ):
        raise InvalidPSGCAddressError


def submit_attendance(
    db: Session,
    event_code: str,
    payload: AttendanceSubmissionRequest,
    signature_image: UploadFile | None,
    settings: Settings,
) -> AttendanceSubmissionResult:
    event = db.scalar(
        select(Event).where(Event.event_code == event_code)
    )
    if event is None or event.event_status == "archived":
        raise PublicEventNotFoundError
    if event.event_status != "open":
        raise EventNotOpenError

    duplicate_id = db.scalar(
        select(AttendanceRecord.attendance_id).where(
            AttendanceRecord.event_id == event.event_id,
            func.lower(AttendanceRecord.email) == str(payload.email).lower(),
        )
    )
    if duplicate_id is not None:
        raise DuplicateAttendanceError

    _validate_psgc_address(db, payload)
    has_uploaded_signature = (
        signature_image is not None and bool(signature_image.filename)
    )
    if payload.signature_text is None and not has_uploaded_signature:
        raise SignatureRequiredError

    signature_image_path = None
    if has_uploaded_signature:
        signature_image_path = save_signature_image(
            signature_image,
            settings.signature_directory,
            event.event_id,
            settings.signature_max_bytes,
        )

    attendance = AttendanceRecord(
        event_id=event.event_id,
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        suffix=payload.suffix,
        affiliation=payload.affiliation,
        designation_category=payload.designation_category,
        sex=payload.sex,
        email=str(payload.email),
        consent_documentation_publication=(
            payload.consent_documentation_publication
        ),
        consent_database_processing=payload.consent_database_processing,
        signature_text=payload.signature_text,
        signature_image_path=signature_image_path,
        attendance_status="valid",
        duplicate_flag=False,
    )
    if payload.has_address:
        attendance.address = AttendanceRecordAddress(
            region_code=payload.region_code,
            province_code=payload.province_code,
            city_municipality_code=payload.city_municipality_code,
            barangay_code=payload.barangay_code,
            street_address=payload.street_address,
            postal_code=payload.postal_code,
        )

    try:
        db.add(attendance)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        remove_signature_image(
            settings.signature_directory,
            signature_image_path,
        )
        if _is_duplicate_entry_error(exc):
            raise DuplicateAttendanceError from exc
        raise
    except Exception:
        db.rollback()
        remove_signature_image(
            settings.signature_directory,
            signature_image_path,
        )
        raise

    db.refresh(attendance)
    return AttendanceSubmissionResult(attendance=attendance, event=event)
