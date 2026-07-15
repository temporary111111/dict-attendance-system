"""Super Admin writes para sa normalized PSGC hierarchy."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import PSGCBarangay, PSGCCityMunicipality, PSGCProvince, PSGCRegion
from app.schemas.psgc_admin import (
    UpsertPSGCBarangayRequest,
    UpsertPSGCCityMunicipalityRequest,
    UpsertPSGCProvinceRequest,
    UpsertPSGCRegionRequest,
)
from app.services.audit_service import build_audit_log


class InvalidPSGCParentError(Exception):
    """Raised kapag missing, inactive, o hindi magkatugma ang parent."""


def _commit_and_refresh(db: Session, record) -> None:
    """Sine-save ang PSGC record at nililinis ang transaction kapag nag-fail."""
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(record)


def psgc_summary(db: Session) -> dict[str, int]:
    return {
        "regions": int(db.scalar(select(func.count(PSGCRegion.region_code))) or 0),
        "provinces": int(db.scalar(select(func.count(PSGCProvince.province_code))) or 0),
        "cities_municipalities": int(
            db.scalar(
                select(func.count(PSGCCityMunicipality.city_municipality_code))
            )
            or 0
        ),
        "barangays": int(db.scalar(select(func.count(PSGCBarangay.barangay_code))) or 0),
    }


def _audit(db: Session, user_id: int, entity_type: str, code: str, created: bool) -> None:
    db.add(
        build_audit_log(
            user_id=user_id,
            action="created_psgc_record" if created else "updated_psgc_record",
            entity_type=entity_type,
            entity_id=None,
            description=f"{'Created' if created else 'Updated'} {entity_type} code {code}.",
            old_values=None,
            new_values={"code": code},
            ip_address=None,
            user_agent=None,
        )
    )


def upsert_region(db: Session, payload: UpsertPSGCRegionRequest, user_id: int):
    record = db.get(PSGCRegion, payload.region_code)
    created = record is None
    if record is None:
        record = PSGCRegion(region_code=payload.region_code)
    record.region_name = payload.region_name
    record.is_active = True
    db.add(record)
    _audit(db, user_id, "psgc_region", payload.region_code, created)
    _commit_and_refresh(db, record)
    return record


def upsert_province(db: Session, payload: UpsertPSGCProvinceRequest, user_id: int):
    region = db.get(PSGCRegion, payload.region_code)
    if region is None or not region.is_active:
        raise InvalidPSGCParentError
    record = db.get(PSGCProvince, payload.province_code)
    created = record is None
    if record is None:
        record = PSGCProvince(province_code=payload.province_code)
    record.region_code = payload.region_code
    record.province_name = payload.province_name
    record.is_active = True
    db.add(record)
    _audit(db, user_id, "psgc_province", payload.province_code, created)
    _commit_and_refresh(db, record)
    return record


def upsert_city_municipality(
    db: Session,
    payload: UpsertPSGCCityMunicipalityRequest,
    user_id: int,
):
    region = db.get(PSGCRegion, payload.region_code)
    if region is None or not region.is_active:
        raise InvalidPSGCParentError
    if payload.province_code is not None:
        province = db.get(PSGCProvince, payload.province_code)
        if (
            province is None
            or not province.is_active
            or province.region_code != payload.region_code
        ):
            raise InvalidPSGCParentError
    record = db.get(PSGCCityMunicipality, payload.city_municipality_code)
    created = record is None
    if record is None:
        record = PSGCCityMunicipality(
            city_municipality_code=payload.city_municipality_code
        )
    record.region_code = payload.region_code
    record.province_code = payload.province_code
    record.city_municipality_name = payload.city_municipality_name
    record.city_municipality_type = payload.city_municipality_type
    record.is_active = True
    db.add(record)
    _audit(
        db,
        user_id,
        "psgc_city_municipality",
        payload.city_municipality_code,
        created,
    )
    _commit_and_refresh(db, record)
    return record


def upsert_barangay(db: Session, payload: UpsertPSGCBarangayRequest, user_id: int):
    city = db.get(PSGCCityMunicipality, payload.city_municipality_code)
    if city is None or not city.is_active:
        raise InvalidPSGCParentError
    record = db.get(PSGCBarangay, payload.barangay_code)
    created = record is None
    if record is None:
        record = PSGCBarangay(barangay_code=payload.barangay_code)
    record.city_municipality_code = payload.city_municipality_code
    record.barangay_name = payload.barangay_name
    record.is_active = True
    db.add(record)
    _audit(db, user_id, "psgc_barangay", payload.barangay_code, created)
    _commit_and_refresh(db, record)
    return record
