"""Business rules para sa DICT organizational unit hierarchy."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import OrganizationalUnit
from app.schemas.reference_data import CreateOrganizationalUnitRequest


class UnitCodeAlreadyExistsError(Exception):
    """Raised kapag ginagamit na ang supplied organizational unit code."""


class InvalidParentUnitError(Exception):
    """Raised kapag missing o inactive ang selected parent unit."""


def create_organizational_unit(
    db: Session,
    payload: CreateOrganizationalUnitRequest,
) -> OrganizationalUnit:
    """Vine-validate ang hierarchy at sine-save ang bagong active unit."""
    if payload.unit_code is not None:
        existing_unit_id = db.scalar(
            select(OrganizationalUnit.org_unit_id).where(
                func.lower(OrganizationalUnit.unit_code)
                == payload.unit_code.lower()
            )
        )
        if existing_unit_id is not None:
            raise UnitCodeAlreadyExistsError

    if payload.parent_unit_id is not None:
        parent = db.get(OrganizationalUnit, payload.parent_unit_id)
        if parent is None or not parent.is_active:
            raise InvalidParentUnitError

    unit = OrganizationalUnit(
        parent_unit_id=payload.parent_unit_id,
        unit_name=payload.unit_name,
        unit_type=payload.unit_type,
        unit_code=payload.unit_code,
        is_active=True,
    )
    db.add(unit)

    try:
        db.commit()
    except IntegrityError as exc:
        # Unique DB constraint ang final protection kapag sabay ang requests.
        db.rollback()
        raise UnitCodeAlreadyExistsError from exc

    db.refresh(unit)
    return unit

