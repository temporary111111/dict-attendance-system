"""Safe reads at manual corrections para sa local PSGC master data."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Literal

from sqlalchemy import func, literal, or_, select, union_all
from sqlalchemy.orm import Session

from app.models import (
    AttendanceRecordAddress,
    PSGCBarangay,
    PSGCCityMunicipality,
    PSGCProvince,
    PSGCRegion,
)
from app.schemas.psgc_management import PSGCLevel, PSGCStatusFilter
from app.services.audit_service import build_audit_log


class PsgcRecordNotFoundError(Exception):
    """Raised kapag walang matching PSGC record sa requested level/code."""


class PsgcCodeAlreadyExistsError(Exception):
    """Raised kapag may ibang row na gumagamit na ng replacement code."""


class PsgcRecordInUseError(Exception):
    """Raised kapag may child o attendance-address dependency ang row."""

    def __init__(
        self,
        *,
        child_count: int,
        attendance_address_reference_count: int,
    ) -> None:
        self.child_count = child_count
        self.attendance_address_reference_count = attendance_address_reference_count
        super().__init__("The PSGC record is still in use.")


@dataclass(frozen=True)
class PsgcLevelDefinition:
    model: type
    code_attribute: str
    name_attribute: str
    entity_type: str


@dataclass
class PsgcPage:
    items: list[dict[str, Any]]
    page: int
    page_size: int
    total_items: int
    total_pages: int


LEVELS: dict[PSGCLevel, PsgcLevelDefinition] = {
    "region": PsgcLevelDefinition(
        model=PSGCRegion,
        code_attribute="region_code",
        name_attribute="region_name",
        entity_type="psgc_region",
    ),
    "province": PsgcLevelDefinition(
        model=PSGCProvince,
        code_attribute="province_code",
        name_attribute="province_name",
        entity_type="psgc_province",
    ),
    "city_municipality": PsgcLevelDefinition(
        model=PSGCCityMunicipality,
        code_attribute="city_municipality_code",
        name_attribute="city_municipality_name",
        entity_type="psgc_city_municipality",
    ),
    "barangay": PsgcLevelDefinition(
        model=PSGCBarangay,
        code_attribute="barangay_code",
        name_attribute="barangay_name",
        entity_type="psgc_barangay",
    ),
}


def _definition(level: PSGCLevel) -> PsgcLevelDefinition:
    return LEVELS[level]


def _record_code(level: PSGCLevel, record) -> str:
    return getattr(record, _definition(level).code_attribute)


def _record_name(level: PSGCLevel, record) -> str:
    return getattr(record, _definition(level).name_attribute)


def _load_record(db: Session, level: PSGCLevel, code: str):
    record = db.get(_definition(level).model, code)
    if record is None:
        raise PsgcRecordNotFoundError
    return record


def _base_row_statement(level: PSGCLevel):
    """Uniform columns para puwedeng i-page at i-union ang iba't ibang level."""
    definition = _definition(level)
    model = definition.model
    code_column = getattr(model, definition.code_attribute)
    name_column = getattr(model, definition.name_attribute)

    if level == "region":
        return select(
            literal(level).label("level"),
            code_column.label("code"),
            name_column.label("name"),
            model.is_active.label("is_active"),
            literal(None).label("parent_label"),
            literal(None).label("city_municipality_type"),
        )
    if level == "province":
        return select(
            literal(level).label("level"),
            code_column.label("code"),
            name_column.label("name"),
            model.is_active.label("is_active"),
            PSGCRegion.region_name.label("parent_label"),
            literal(None).label("city_municipality_type"),
        ).join(PSGCRegion, PSGCProvince.region_code == PSGCRegion.region_code)
    if level == "city_municipality":
        return (
            select(
                literal(level).label("level"),
                code_column.label("code"),
                name_column.label("name"),
                model.is_active.label("is_active"),
                func.coalesce(
                    PSGCProvince.province_name,
                    PSGCRegion.region_name,
                ).label("parent_label"),
                PSGCCityMunicipality.city_municipality_type.label(
                    "city_municipality_type"
                ),
            )
            .join(PSGCRegion, PSGCCityMunicipality.region_code == PSGCRegion.region_code)
            .outerjoin(
                PSGCProvince,
                PSGCCityMunicipality.province_code == PSGCProvince.province_code,
            )
        )
    return select(
        literal(level).label("level"),
        code_column.label("code"),
        name_column.label("name"),
        model.is_active.label("is_active"),
        PSGCCityMunicipality.city_municipality_name.label("parent_label"),
        literal(None).label("city_municipality_type"),
    ).join(
        PSGCCityMunicipality,
        PSGCBarangay.city_municipality_code
        == PSGCCityMunicipality.city_municipality_code,
    )


def _filter_statement(
    statement,
    *,
    status: PSGCStatusFilter,
    search: str | None,
):
    rows = statement.subquery()
    filters = []
    if status == "active":
        filters.append(rows.c.is_active.is_(True))
    elif status == "inactive":
        filters.append(rows.c.is_active.is_(False))
    if search:
        pattern = f"%{search.strip().lower()}%"
        filters.append(
            or_(
                func.lower(rows.c.code).like(pattern),
                func.lower(rows.c.name).like(pattern),
            )
        )
    return rows, filters


def _paginate_rows(
    db: Session,
    statement,
    *,
    page: int,
    page_size: int,
    status: PSGCStatusFilter,
    search: str | None,
) -> PsgcPage:
    rows, filters = _filter_statement(statement, status=status, search=search)
    total_items = int(
        db.scalar(select(func.count()).select_from(rows).where(*filters)) or 0
    )
    result = db.execute(
        select(*rows.c)
        .where(*filters)
        .order_by(func.lower(rows.c.name), rows.c.code)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [
        {
            "level": row["level"],
            "code": row["code"],
            "name": row["name"],
            "is_active": bool(row["is_active"]),
            "parent_label": row["parent_label"],
            "city_municipality_type": row["city_municipality_type"],
        }
        for row in result.mappings().all()
    ]
    return PsgcPage(
        items=items,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=ceil(total_items / page_size) if total_items else 0,
    )


def list_regions(
    db: Session,
    *,
    page: int,
    page_size: int,
    status: PSGCStatusFilter,
    search: str | None,
) -> PsgcPage:
    return _paginate_rows(
        db,
        _base_row_statement("region"),
        page=page,
        page_size=page_size,
        status=status,
        search=search,
    )


def list_children(
    db: Session,
    *,
    level: Literal["region", "province", "city_municipality"],
    code: str,
    page: int,
    page_size: int,
    status: PSGCStatusFilter,
    search: str | None,
) -> PsgcPage:
    _load_record(db, level, code)
    if level == "region":
        provinces = _base_row_statement("province").where(
            PSGCProvince.region_code == code
        )
        direct_cities = _base_row_statement("city_municipality").where(
            PSGCCityMunicipality.region_code == code,
            PSGCCityMunicipality.province_code.is_(None),
        )
        statement = union_all(provinces, direct_cities)
    elif level == "province":
        statement = _base_row_statement("city_municipality").where(
            PSGCCityMunicipality.province_code == code
        )
    else:
        statement = _base_row_statement("barangay").where(
            PSGCBarangay.city_municipality_code == code
        )
    return _paginate_rows(
        db,
        statement,
        page=page,
        page_size=page_size,
        status=status,
        search=search,
    )


def search_psgc(
    db: Session,
    *,
    query: str,
    level: PSGCLevel | None,
    page: int,
    page_size: int,
    status: PSGCStatusFilter,
) -> PsgcPage:
    statement = _base_row_statement(level) if level else union_all(
        _base_row_statement("region"),
        _base_row_statement("province"),
        _base_row_statement("city_municipality"),
        _base_row_statement("barangay"),
    )
    result = _paginate_rows(
        db,
        statement,
        page=page,
        page_size=page_size,
        status=status,
        search=query,
    )
    for item in result.items:
        item["path_label"] = " > ".join(
            segment["name"] for segment in _path_for_record(db, item["level"], item["code"])
        )
    return result


def _path_for_record(
    db: Session,
    level: PSGCLevel,
    code: str,
) -> list[dict[str, str]]:
    record = _load_record(db, level, code)
    if level == "region":
        return [{"level": level, "code": code, "name": record.region_name}]
    if level == "province":
        region = db.get(PSGCRegion, record.region_code)
        return [
            *(
                [
                    {
                        "level": "region",
                        "code": region.region_code,
                        "name": region.region_name,
                    }
                ]
                if region
                else []
            ),
            {"level": level, "code": code, "name": record.province_name},
        ]
    if level == "city_municipality":
        region = db.get(PSGCRegion, record.region_code)
        province = (
            db.get(PSGCProvince, record.province_code)
            if record.province_code is not None
            else None
        )
        return [
            *(
                [
                    {
                        "level": "region",
                        "code": region.region_code,
                        "name": region.region_name,
                    }
                ]
                if region
                else []
            ),
            *(
                [
                    {
                        "level": "province",
                        "code": province.province_code,
                        "name": province.province_name,
                    }
                ]
                if province
                else []
            ),
            {
                "level": level,
                "code": code,
                "name": record.city_municipality_name,
            },
        ]
    city = db.get(PSGCCityMunicipality, record.city_municipality_code)
    city_path = (
        _path_for_record(db, "city_municipality", city.city_municipality_code)
        if city
        else []
    )
    return [
        *city_path,
        {"level": level, "code": code, "name": record.barangay_name},
    ]


def _dependency_counts(
    db: Session,
    level: PSGCLevel,
    code: str,
) -> tuple[int, int]:
    if level == "region":
        direct_children = union_all(
            select(PSGCProvince.province_code).where(
                PSGCProvince.region_code == code
            ),
            select(PSGCCityMunicipality.city_municipality_code).where(
                PSGCCityMunicipality.region_code == code,
                PSGCCityMunicipality.province_code.is_(None),
            ),
        ).subquery()
        child_count = int(
            db.scalar(select(func.count()).select_from(direct_children)) or 0
        )
        address_count = int(
            db.scalar(
                select(func.count())
                .select_from(AttendanceRecordAddress)
                .where(AttendanceRecordAddress.region_code == code)
            )
            or 0
        )
        return child_count, address_count
    if level == "province":
        child_statement = (
            select(func.count())
            .select_from(PSGCCityMunicipality)
            .where(PSGCCityMunicipality.province_code == code)
        )
        address_column = AttendanceRecordAddress.province_code
    elif level == "city_municipality":
        child_statement = (
            select(func.count())
            .select_from(PSGCBarangay)
            .where(PSGCBarangay.city_municipality_code == code)
        )
        address_column = AttendanceRecordAddress.city_municipality_code
    else:
        child_statement = select(literal(0))
        address_column = AttendanceRecordAddress.barangay_code
    child_count = int(db.scalar(child_statement) or 0)
    address_count = int(
        db.scalar(
            select(func.count())
            .select_from(AttendanceRecordAddress)
            .where(address_column == code)
        )
        or 0
    )
    return child_count, address_count


def get_record_detail(db: Session, *, level: PSGCLevel, code: str) -> dict[str, Any]:
    record = _load_record(db, level, code)
    child_count, address_count = _dependency_counts(db, level, code)
    result = {
        "level": level,
        "code": _record_code(level, record),
        "name": _record_name(level, record),
        "is_active": bool(record.is_active),
        "parent_label": None,
        "city_municipality_type": getattr(record, "city_municipality_type", None),
        "path": _path_for_record(db, level, code),
        "dependencies": {
            "child_count": child_count,
            "attendance_address_reference_count": address_count,
        },
    }
    if len(result["path"]) > 1:
        result["parent_label"] = result["path"][-2]["name"]
    return result


def _raise_if_in_use(db: Session, level: PSGCLevel, code: str) -> None:
    child_count, address_count = _dependency_counts(db, level, code)
    if child_count or address_count:
        raise PsgcRecordInUseError(
            child_count=child_count,
            attendance_address_reference_count=address_count,
        )


def _commit(db: Session, record=None) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    if record is not None:
        db.refresh(record)


def _audit(
    db: Session,
    *,
    user_id: int,
    level: PSGCLevel,
    action: str,
    code: str,
    reason: str,
    old_values: dict[str, Any] | None,
    new_values: dict[str, Any] | None,
) -> None:
    db.add(
        build_audit_log(
            user_id=user_id,
            action=action,
            entity_type=_definition(level).entity_type,
            entity_id=None,
            description=f"{action} for {level} {code}. Reason: {reason}",
            old_values=old_values,
            new_values=new_values,
            ip_address=None,
            user_agent=None,
        )
    )


def update_name(
    db: Session,
    *,
    level: PSGCLevel,
    code: str,
    name: str,
    reason: str,
    user_id: int,
):
    record = _load_record(db, level, code)
    old_name = _record_name(level, record)
    setattr(record, _definition(level).name_attribute, name)
    db.add(record)
    _audit(
        db,
        user_id=user_id,
        level=level,
        action="updated_psgc_name",
        code=code,
        reason=reason,
        old_values={"name": old_name},
        new_values={"name": name},
    )
    _commit(db, record)
    return record


def update_status(
    db: Session,
    *,
    level: PSGCLevel,
    code: str,
    is_active: bool,
    reason: str,
    user_id: int,
):
    record = _load_record(db, level, code)
    old_status = bool(record.is_active)
    record.is_active = is_active
    db.add(record)
    _audit(
        db,
        user_id=user_id,
        level=level,
        action="updated_psgc_status",
        code=code,
        reason=reason,
        old_values={"is_active": old_status},
        new_values={"is_active": is_active},
    )
    _commit(db, record)
    return record


def update_code(
    db: Session,
    *,
    level: PSGCLevel,
    code: str,
    new_code: str,
    reason: str,
    user_id: int,
):
    record = _load_record(db, level, code)
    if new_code != code and db.get(_definition(level).model, new_code) is not None:
        raise PsgcCodeAlreadyExistsError
    _raise_if_in_use(db, level, code)
    setattr(record, _definition(level).code_attribute, new_code)
    db.add(record)
    _audit(
        db,
        user_id=user_id,
        level=level,
        action="updated_psgc_code",
        code=code,
        reason=reason,
        old_values={"code": code},
        new_values={"code": new_code},
    )
    _commit(db, record)
    return record


def delete_record(
    db: Session,
    *,
    level: PSGCLevel,
    code: str,
    reason: str,
    user_id: int,
) -> None:
    record = _load_record(db, level, code)
    _raise_if_in_use(db, level, code)
    _audit(
        db,
        user_id=user_id,
        level=level,
        action="deleted_psgc_record",
        code=code,
        reason=reason,
        old_values={"code": code, "name": _record_name(level, record)},
        new_values=None,
    )
    db.delete(record)
    _commit(db)
