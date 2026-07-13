"""Active PSGC dropdown queries para sa fixed public attendance form."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    PSGCBarangay,
    PSGCCityMunicipality,
    PSGCProvince,
    PSGCRegion,
)


def list_active_regions(db: Session) -> list[PSGCRegion]:
    return list(
        db.scalars(
            select(PSGCRegion)
            .where(PSGCRegion.is_active.is_(True))
            .order_by(PSGCRegion.region_name)
        ).all()
    )


def list_active_provinces(
    db: Session,
    region_code: str,
) -> list[PSGCProvince]:
    return list(
        db.scalars(
            select(PSGCProvince)
            .where(
                PSGCProvince.region_code == region_code,
                PSGCProvince.is_active.is_(True),
            )
            .order_by(PSGCProvince.province_name)
        ).all()
    )


def list_active_cities_municipalities(
    db: Session,
    region_code: str,
    province_code: str | None,
) -> list[PSGCCityMunicipality]:
    statement = select(PSGCCityMunicipality).where(
        PSGCCityMunicipality.region_code == region_code,
        PSGCCityMunicipality.is_active.is_(True),
    )
    if province_code is not None:
        statement = statement.where(
            PSGCCityMunicipality.province_code == province_code
        )
    return list(
        db.scalars(
            statement.order_by(PSGCCityMunicipality.city_municipality_name)
        ).all()
    )


def list_active_barangays(
    db: Session,
    city_municipality_code: str,
) -> list[PSGCBarangay]:
    return list(
        db.scalars(
            select(PSGCBarangay)
            .where(
                PSGCBarangay.city_municipality_code == city_municipality_code,
                PSGCBarangay.is_active.is_(True),
            )
            .order_by(PSGCBarangay.barangay_name)
        ).all()
    )
