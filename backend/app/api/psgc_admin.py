"""Protected PSGC reference-data management routes."""

from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
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
from app.services.psgc_import_service import (
    PSGCImportValidationError,
    import_psgc_workbook,
    preview_psgc_workbook,
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


async def _read_psgc_upload(file: UploadFile, max_bytes: int) -> tuple[bytes, str]:
    """Binabasa lang ang reasonable-size Excel file bago ito i-validate."""
    file_name = file.filename or "PSGC-masterlist.xlsx"
    if not file_name.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "INVALID_PSGC_IMPORT_FILE",
                "Upload an official PSGC Excel (.xlsx) file.",
            ),
        )
    contents = await file.read(max_bytes + 1)
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "INVALID_PSGC_IMPORT_FILE",
                "The PSGC Excel file exceeds the allowed upload size.",
            ),
        )
    return contents, file_name


@router.post("/imports/preview")
async def preview_psgc_import(
    request: Request,
    source_version: Annotated[str, Form(min_length=1, max_length=120)],
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    """Preview lang ito; walang mababago sa PSGC lookup tables."""
    contents, file_name = await _read_psgc_upload(
        file,
        request.app.state.settings.psgc_import_max_bytes,
    )
    try:
        preview = preview_psgc_workbook(contents, file_name)
        message = "PSGC file is ready to import."
    except PSGCImportValidationError as error:
        preview = error.preview
        message = "PSGC file needs correction before import."
    preview["source_version"] = source_version.strip()
    return success_response(preview, message)


@router.post("/imports/apply")
async def apply_psgc_import(
    request: Request,
    source_version: Annotated[str, Form(min_length=1, max_length=120)],
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    """Imports only a workbook that passes the same validation as preview."""
    contents, file_name = await _read_psgc_upload(
        file,
        request.app.state.settings.psgc_import_max_bytes,
    )
    try:
        result = import_psgc_workbook(
            db,
            contents,
            file_name,
            source_version.strip(),
            current_user.user_id,
        )
    except PSGCImportValidationError as error:
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "INVALID_PSGC_IMPORT",
                "PSGC file validation failed. Preview and correct the file first.",
                {"file": error.errors},
            ),
        ) from error
    return success_response(result, "PSGC masterlist imported.")


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
