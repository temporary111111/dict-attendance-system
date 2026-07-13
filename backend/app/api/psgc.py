"""Public active PSGC lookup routes para sa address dropdowns."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.schemas.public_attendance import (
    PSGCBarangayListResponse,
    PSGCCityMunicipalityListResponse,
    PSGCProvinceListResponse,
    PSGCRegionListResponse,
)
from app.services.psgc_service import (
    list_active_barangays,
    list_active_cities_municipalities,
    list_active_provinces,
    list_active_regions,
)

router = APIRouter(prefix="/psgc", tags=["public PSGC"])


@router.get("/regions", response_model=PSGCRegionListResponse)
def list_regions(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    return success_response(list_active_regions(db), "PSGC regions retrieved.")


@router.get("/provinces", response_model=PSGCProvinceListResponse)
def list_provinces(
    region_code: Annotated[
        str,
        Query(alias="regionCode", min_length=1, max_length=10),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    return success_response(
        list_active_provinces(db, region_code),
        "PSGC provinces retrieved.",
    )


@router.get(
    "/cities-municipalities",
    response_model=PSGCCityMunicipalityListResponse,
)
def list_cities_municipalities(
    region_code: Annotated[
        str,
        Query(alias="regionCode", min_length=1, max_length=10),
    ],
    db: Annotated[Session, Depends(get_db)],
    province_code: Annotated[
        str | None,
        Query(alias="provinceCode", min_length=1, max_length=10),
    ] = None,
) -> dict[str, Any]:
    return success_response(
        list_active_cities_municipalities(
            db,
            region_code,
            province_code,
        ),
        "PSGC cities and municipalities retrieved.",
    )


@router.get("/barangays", response_model=PSGCBarangayListResponse)
def list_barangays(
    city_municipality_code: Annotated[
        str,
        Query(alias="cityMunicipalityCode", min_length=1, max_length=10),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    return success_response(
        list_active_barangays(db, city_municipality_code),
        "PSGC barangays retrieved.",
    )
