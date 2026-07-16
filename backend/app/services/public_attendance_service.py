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
from app.models.attendance_fields import ATTENDANCE_FIELD_KEYS
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
    """Raised kapag walang drawn o uploaded signature."""


class AttendanceFieldValidationError(Exception):
    def __init__(self, fields: dict[str, str]):
        self.fields = fields


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
        .options(
            selectinload(Event.program),
            selectinload(Event.attendance_field_settings),
        )
        .where(
            Event.event_code == event_code,
            Event.event_status != "archived",
        )
    )
    if event is None:
        raise PublicEventNotFoundError
    return event


def attendance_field_requirements(event: Event) -> dict[str, bool]:
    """Ginagawang validated map ang per-event fixed field snapshot."""
    requirements = {
        setting.field_key: bool(setting.is_required)
        for setting in event.attendance_field_settings
    }
    if set(requirements) != set(ATTENDANCE_FIELD_KEYS):
        raise RuntimeError("Event attendance field settings are incomplete.")
    return requirements


def attendance_field_visibility(event: Event) -> dict[str, bool]:
    """Ginagawang validated map ang show/hide snapshot ng event."""
    visibility = {
        setting.field_key: bool(getattr(setting, "is_visible", True))
        for setting in event.attendance_field_settings
    }
    if set(visibility) != set(ATTENDANCE_FIELD_KEYS):
        raise RuntimeError("Event attendance field visibility is incomplete.")
    return visibility


def _validate_event_field_requirements(
    payload: AttendanceSubmissionRequest,
    requirements: dict[str, bool],
    visibility: dict[str, bool],
    *,
    has_uploaded_signature: bool,
) -> None:
    missing: dict[str, str] = {}
    direct_fields = (
        "middle_name",
        "suffix",
        "affiliation",
        "designation_category",
        "sex",
        "consent_documentation_publication",
        "street_address",
        "postal_code",
    )
    for field_key in direct_fields:
        value = getattr(payload, field_key)
        is_missing = value is None
        if field_key == "consent_documentation_publication":
            # Required checkbox ito, kaya hindi sapat na may false value lang.
            is_missing = value is not True
        if (
            visibility[field_key]
            and requirements[field_key]
            and is_missing
        ):
            missing[field_key] = "This field is required for this event."

    if visibility["psgc_address"] and requirements["psgc_address"]:
        for field_key in (
            "region_code",
            "city_municipality_code",
            "barangay_code",
        ):
            if getattr(payload, field_key) is None:
                missing[field_key] = "This field is required for this event."

    if visibility["signature"] and requirements["signature"] and not has_uploaded_signature:
        raise SignatureRequiredError
    if missing:
        raise AttendanceFieldValidationError(missing)


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

    requirements = attendance_field_requirements(event)
    visibility = attendance_field_visibility(event)
    has_uploaded_signature = (
        visibility["signature"]
        and signature_image is not None
        and bool(signature_image.filename)
    )
    _validate_event_field_requirements(
        payload,
        requirements,
        visibility,
        has_uploaded_signature=has_uploaded_signature,
    )

    if visibility["psgc_address"]:
        _validate_psgc_address(db, payload)

    duplicate_id = db.scalar(
        select(AttendanceRecord.attendance_id).where(
            AttendanceRecord.event_id == event.event_id,
            func.lower(AttendanceRecord.email) == str(payload.email).lower(),
        )
    )
    if duplicate_id is not None:
        raise DuplicateAttendanceError

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
        middle_name=payload.middle_name if visibility["middle_name"] else None,
        last_name=payload.last_name,
        suffix=payload.suffix if visibility["suffix"] else None,
        affiliation=payload.affiliation if visibility["affiliation"] else None,
        designation_category=(
            payload.designation_category
            if visibility["designation_category"]
            else None
        ),
        sex=payload.sex if visibility["sex"] else None,
        email=str(payload.email),
        consent_documentation_publication=bool(
            payload.consent_documentation_publication
            if visibility["consent_documentation_publication"]
            else False
        ),
        consent_database_processing=payload.consent_database_processing,
        # Legacy column ito; new public attendance uses only signature images.
        signature_text=None,
        signature_image_path=signature_image_path,
        attendance_status="valid",
        duplicate_flag=False,
    )
    if visibility["psgc_address"] and payload.has_address:
        attendance.address = AttendanceRecordAddress(
            region_code=payload.region_code,
            province_code=payload.province_code,
            city_municipality_code=payload.city_municipality_code,
            barangay_code=payload.barangay_code,
            street_address=(
                payload.street_address if visibility["street_address"] else None
            ),
            postal_code=(
                payload.postal_code if visibility["postal_code"] else None
            ),
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
