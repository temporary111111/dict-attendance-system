"""Business rules para sa DICT organizational unit hierarchy."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import OrganizationalUnit
from app.schemas.reference_data import (
    CreateOrganizationalUnitRequest,
    UpdateOrganizationalUnitRequest,
)


class UnitCodeAlreadyExistsError(Exception):
    """Raised kapag ginagamit na ang supplied organizational unit code."""


class InvalidParentUnitError(Exception):
    """Raised kapag missing o inactive ang selected parent unit."""


class OrganizationalUnitNotFoundError(Exception):
    """Raised kapag walang organizational unit para sa supplied ID."""


class CircularUnitHierarchyError(Exception):
    """Raised kapag gagawa ng self-parent o circular hierarchy ang update."""


class UnitHasActiveChildrenError(Exception):
    """Raised kapag ide-deactivate ang unit na may active child units."""


def _unit_code_is_in_use(
    db: Session,
    unit_code: str,
    *,
    exclude_unit_id: int | None = None,
) -> bool:
    """Case-insensitive lookup na puwedeng hindi isama ang current unit."""
    statement = select(OrganizationalUnit.org_unit_id).where(
        func.lower(OrganizationalUnit.unit_code) == unit_code.lower()
    )
    if exclude_unit_id is not None:
        statement = statement.where(
            OrganizationalUnit.org_unit_id != exclude_unit_id
        )
    return db.scalar(statement) is not None


def _get_active_parent(
    db: Session,
    parent_unit_id: int,
) -> OrganizationalUnit:
    parent = db.get(OrganizationalUnit, parent_unit_id)
    if parent is None or not parent.is_active:
        raise InvalidParentUnitError
    return parent


def _ensure_no_hierarchy_cycle(
    db: Session,
    unit_id: int,
    proposed_parent: OrganizationalUnit,
) -> None:
    """Inaakyat ang parent chain para hindi mapasailalim sa sariling child."""
    current = proposed_parent
    visited_unit_ids: set[int] = set()

    while current is not None:
        if (
            current.org_unit_id == unit_id
            or current.org_unit_id in visited_unit_ids
        ):
            raise CircularUnitHierarchyError

        visited_unit_ids.add(current.org_unit_id)
        if current.parent_unit_id is None:
            return
        current = db.get(OrganizationalUnit, current.parent_unit_id)


def _commit_unit_write(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        # Unique constraint ang final protection kapag sabay ang requests.
        db.rollback()
        raise UnitCodeAlreadyExistsError from exc


def create_organizational_unit(
    db: Session,
    payload: CreateOrganizationalUnitRequest,
) -> OrganizationalUnit:
    """Vine-validate ang hierarchy at sine-save ang bagong active unit."""
    if payload.unit_code is not None:
        if _unit_code_is_in_use(db, payload.unit_code):
            raise UnitCodeAlreadyExistsError

    if payload.parent_unit_id is not None:
        _get_active_parent(db, payload.parent_unit_id)

    unit = OrganizationalUnit(
        parent_unit_id=payload.parent_unit_id,
        unit_name=payload.unit_name,
        unit_type=payload.unit_type,
        unit_code=payload.unit_code,
        is_active=True,
    )
    db.add(unit)

    _commit_unit_write(db)
    db.refresh(unit)
    return unit


def update_organizational_unit(
    db: Session,
    unit_id: int,
    payload: UpdateOrganizationalUnitRequest,
) -> OrganizationalUnit:
    """Ina-apply ang supplied fields matapos i-check ang hierarchy rules."""
    unit = db.get(OrganizationalUnit, unit_id)
    if unit is None:
        raise OrganizationalUnitNotFoundError

    supplied_fields = payload.model_fields_set

    if "unit_code" in supplied_fields and payload.unit_code is not None:
        if _unit_code_is_in_use(
            db,
            payload.unit_code,
            exclude_unit_id=unit_id,
        ):
            raise UnitCodeAlreadyExistsError

    if "parent_unit_id" in supplied_fields:
        if payload.parent_unit_id is None:
            unit.parent_unit_id = None
        else:
            parent = _get_active_parent(db, payload.parent_unit_id)
            _ensure_no_hierarchy_cycle(db, unit_id, parent)
            unit.parent_unit_id = payload.parent_unit_id

    if "is_active" in supplied_fields and payload.is_active is False:
        active_child_id = db.scalar(
            select(OrganizationalUnit.org_unit_id)
            .where(
                OrganizationalUnit.parent_unit_id == unit_id,
                OrganizationalUnit.is_active.is_(True),
            )
            .limit(1)
        )
        if active_child_id is not None:
            raise UnitHasActiveChildrenError

    if "is_active" in supplied_fields and payload.is_active is True:
        if unit.parent_unit_id is not None:
            _get_active_parent(db, unit.parent_unit_id)

    if "unit_name" in supplied_fields:
        unit.unit_name = payload.unit_name
    if "unit_type" in supplied_fields:
        unit.unit_type = payload.unit_type
    if "unit_code" in supplied_fields:
        unit.unit_code = payload.unit_code
    if "is_active" in supplied_fields:
        unit.is_active = payload.is_active

    _commit_unit_write(db)
    db.refresh(unit)
    return unit
