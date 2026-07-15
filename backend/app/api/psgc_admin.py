"""Protected PSGC reference-data management routes."""

from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.models import User
from app.schemas.psgc_admin import (
    UpsertPSGCBarangayRequest,
    UpsertPSGCCityMunicipalityRequest,
    UpsertPSGCProvinceRequest,
    UpsertPSGCRegionRequest,
)
from app.services.psgc_admin_service import (
    InvalidPSGCParentError,
    psgc_summary,
    upsert_barangay,
    upsert_city_municipality,
    upsert_province,
    upsert_region,
)

router = APIRouter(prefix="/admin/psgc", tags=["PSGC management"])


def _parent_error() -> NoReturn:
    raise HTTPException(
        status_code=422,
        detail=error_response(
            "INVALID_PSGC_PARENT",
            "Select an active and matching PSGC parent record.",
        ),
    )


@router.get("/summary")
def get_psgc_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    return success_response(psgc_summary(db), "PSGC summary retrieved.")


@router.post("/regions")
def save_region(
    payload: UpsertPSGCRegionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    record = upsert_region(db, payload, current_user.user_id)
    return success_response(
        {
            "region_code": record.region_code,
            "region_name": record.region_name,
        },
        "PSGC region saved.",
    )


@router.post("/provinces")
def save_province(
    payload: UpsertPSGCProvinceRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        record = upsert_province(db, payload, current_user.user_id)
    except InvalidPSGCParentError:
        _parent_error()
    return success_response(
        {
            "province_code": record.province_code,
            "province_name": record.province_name,
        },
        "PSGC province saved.",
    )


@router.post("/cities-municipalities")
def save_city_municipality(
    payload: UpsertPSGCCityMunicipalityRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        record = upsert_city_municipality(db, payload, current_user.user_id)
    except InvalidPSGCParentError:
        _parent_error()
    return success_response(
        {
            "city_municipality_code": record.city_municipality_code,
            "city_municipality_name": record.city_municipality_name,
        },
        "PSGC city or municipality saved.",
    )


@router.post("/barangays")
def save_barangay(
    payload: UpsertPSGCBarangayRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        record = upsert_barangay(db, payload, current_user.user_id)
    except InvalidPSGCParentError:
        _parent_error()
    return success_response(
        {
            "barangay_code": record.barangay_code,
            "barangay_name": record.barangay_name,
        },
        "PSGC barangay saved.",
    )
