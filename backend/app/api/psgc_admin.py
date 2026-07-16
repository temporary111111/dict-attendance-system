"""Protected PSGC reference-data management routes."""

from typing import Annotated, Any, NoReturn

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    Request,
    UploadFile,
)
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
from app.schemas.psgc_management import (
    PSGCLevel,
    PSGCStatusFilter,
    PsgcCodeUpdateRequest,
    PsgcDeleteRequest,
    PsgcNameUpdateRequest,
    PsgcStatusUpdateRequest,
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
from app.services.psgc_management_service import (
    PsgcCodeAlreadyExistsError,
    PsgcRecordInUseError,
    PsgcRecordNotFoundError,
    delete_record,
    get_record_detail,
    list_children,
    list_regions,
    search_psgc,
    update_code,
    update_name,
    update_status,
)

router = APIRouter(prefix="/admin/psgc", tags=["PSGC management"])

PSGC_CODE_ATTRIBUTES: dict[PSGCLevel, str] = {
    "region": "region_code",
    "province": "province_code",
    "city_municipality": "city_municipality_code",
    "barangay": "barangay_code",
}


def _parent_error() -> NoReturn:
    raise HTTPException(
        status_code=422,
        detail=error_response(
            "INVALID_PSGC_PARENT",
            "Select an active and matching PSGC parent record.",
        ),
    )


def _record_not_found_error() -> NoReturn:
    raise HTTPException(
        status_code=404,
        detail=error_response("PSGC_RECORD_NOT_FOUND", "PSGC record not found."),
    )


def _record_in_use_error(error: PsgcRecordInUseError) -> NoReturn:
    raise HTTPException(
        status_code=409,
        detail=error_response(
            "PSGC_RECORD_IN_USE",
            "This PSGC record still has child locations or attendance address references.",
            {
                "child_count": error.child_count,
                "attendance_address_reference_count": (
                    error.attendance_address_reference_count
                ),
            },
        ),
    )


def _page_data(page) -> dict[str, Any]:
    return {
        "items": page.items,
        "pagination": {
            "page": page.page,
            "page_size": page.page_size,
            "total_items": page.total_items,
            "total_pages": page.total_pages,
        },
    }


def _updated_record_code(level: PSGCLevel, record) -> str:
    return getattr(record, PSGC_CODE_ATTRIBUTES[level])


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


@router.get("/regions")
def list_psgc_regions(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 25,
    status: PSGCStatusFilter = "active",
    search: Annotated[str | None, Query(min_length=1, max_length=150)] = None,
) -> dict[str, Any]:
    result = list_regions(
        db,
        page=page,
        page_size=page_size,
        status=status,
        search=search.strip() if search else None,
    )
    return success_response(_page_data(result), "PSGC regions retrieved.")


@router.get("/regions/{region_code}/children")
def list_region_children(
    region_code: Annotated[
        str,
        Path(min_length=10, max_length=10, pattern=r"^\d{10}$"),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 25,
    status: PSGCStatusFilter = "active",
    search: Annotated[str | None, Query(min_length=1, max_length=150)] = None,
) -> dict[str, Any]:
    try:
        result = list_children(
            db,
            level="region",
            code=region_code,
            page=page,
            page_size=page_size,
            status=status,
            search=search.strip() if search else None,
        )
    except PsgcRecordNotFoundError:
        _record_not_found_error()
    return success_response(_page_data(result), "PSGC child locations retrieved.")


@router.get("/provinces/{province_code}/children")
def list_province_children(
    province_code: Annotated[
        str,
        Path(min_length=10, max_length=10, pattern=r"^\d{10}$"),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 25,
    status: PSGCStatusFilter = "active",
    search: Annotated[str | None, Query(min_length=1, max_length=150)] = None,
) -> dict[str, Any]:
    try:
        result = list_children(
            db,
            level="province",
            code=province_code,
            page=page,
            page_size=page_size,
            status=status,
            search=search.strip() if search else None,
        )
    except PsgcRecordNotFoundError:
        _record_not_found_error()
    return success_response(_page_data(result), "PSGC child locations retrieved.")


@router.get("/cities-municipalities/{city_municipality_code}/children")
def list_city_municipality_children(
    city_municipality_code: Annotated[
        str,
        Path(min_length=10, max_length=10, pattern=r"^\d{10}$"),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 25,
    status: PSGCStatusFilter = "active",
    search: Annotated[str | None, Query(min_length=1, max_length=150)] = None,
) -> dict[str, Any]:
    try:
        result = list_children(
            db,
            level="city_municipality",
            code=city_municipality_code,
            page=page,
            page_size=page_size,
            status=status,
            search=search.strip() if search else None,
        )
    except PsgcRecordNotFoundError:
        _record_not_found_error()
    return success_response(_page_data(result), "PSGC barangays retrieved.")


@router.get("/search")
def search_psgc_records(
    query: Annotated[str, Query(min_length=1, max_length=150)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
    level: PSGCLevel | None = None,
    status: PSGCStatusFilter = "active",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 25,
) -> dict[str, Any]:
    result = search_psgc(
        db,
        query=query.strip(),
        level=level,
        page=page,
        page_size=page_size,
        status=status,
    )
    return success_response(_page_data(result), "PSGC search results retrieved.")


@router.get("/{level}/{code}")
def get_psgc_record_detail(
    level: PSGCLevel,
    code: Annotated[
        str,
        Path(min_length=10, max_length=10, pattern=r"^\d{10}$"),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        result = get_record_detail(db, level=level, code=code)
    except PsgcRecordNotFoundError:
        _record_not_found_error()
    return success_response(result, "PSGC record retrieved.")


@router.patch("/{level}/{code}/name")
def update_psgc_name(
    level: PSGCLevel,
    code: Annotated[
        str,
        Path(min_length=10, max_length=10, pattern=r"^\d{10}$"),
    ],
    payload: PsgcNameUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        record = update_name(
            db,
            level=level,
            code=code,
            name=payload.name,
            reason=payload.reason,
            user_id=current_user.user_id,
        )
        result = get_record_detail(
            db,
            level=level,
            code=_updated_record_code(level, record),
        )
    except PsgcRecordNotFoundError:
        _record_not_found_error()
    return success_response(result, "PSGC name updated.")


@router.patch("/{level}/{code}/status")
def update_psgc_record_status(
    level: PSGCLevel,
    code: Annotated[
        str,
        Path(min_length=10, max_length=10, pattern=r"^\d{10}$"),
    ],
    payload: PsgcStatusUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        update_status(
            db,
            level=level,
            code=code,
            is_active=payload.is_active,
            reason=payload.reason,
            user_id=current_user.user_id,
        )
        result = get_record_detail(db, level=level, code=code)
    except PsgcRecordNotFoundError:
        _record_not_found_error()
    return success_response(result, "PSGC status updated.")


@router.patch("/{level}/{code}/code")
def update_psgc_code(
    level: PSGCLevel,
    code: Annotated[
        str,
        Path(min_length=10, max_length=10, pattern=r"^\d{10}$"),
    ],
    payload: PsgcCodeUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        record = update_code(
            db,
            level=level,
            code=code,
            new_code=payload.new_code,
            reason=payload.reason,
            user_id=current_user.user_id,
        )
        result = get_record_detail(
            db,
            level=level,
            code=_updated_record_code(level, record),
        )
    except PsgcRecordNotFoundError:
        _record_not_found_error()
    except PsgcCodeAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "PSGC_CODE_ALREADY_EXISTS",
                "Another PSGC record already uses this code.",
            ),
        )
    except PsgcRecordInUseError as error:
        _record_in_use_error(error)
    return success_response(result, "PSGC code updated.")


@router.delete("/{level}/{code}")
def delete_psgc_record(
    level: PSGCLevel,
    code: Annotated[
        str,
        Path(min_length=10, max_length=10, pattern=r"^\d{10}$"),
    ],
    payload: PsgcDeleteRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        delete_record(
            db,
            level=level,
            code=code,
            reason=payload.reason,
            user_id=current_user.user_id,
        )
    except PsgcRecordNotFoundError:
        _record_not_found_error()
    except PsgcRecordInUseError as error:
        _record_in_use_error(error)
    return success_response({"code": code}, "PSGC record permanently deleted.")


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
