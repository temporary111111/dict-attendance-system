"""Reference data at organizational unit management routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.models import OrganizationalUnit, Role
from app.schemas.reference_data import (
    CreateOrganizationalUnitRequest,
    CreateOrganizationalUnitResponse,
    OrganizationalUnitListResponse,
    RoleListResponse,
)
from app.services.organizational_unit_service import (
    InvalidParentUnitError,
    UnitCodeAlreadyExistsError,
    create_organizational_unit,
)

router = APIRouter(
    tags=["reference data"],
    dependencies=[Depends(require_super_admin)],
)


@router.get("/roles", response_model=RoleListResponse)
def list_roles(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Kinukuha ang active roles na pwedeng gamitin sa admin accounts."""
    roles = db.scalars(
        select(Role)
        .where(Role.is_active.is_(True))
        .order_by(Role.role_name)
    ).all()

    return success_response(roles, "Roles retrieved.")


@router.get(
    "/organizational-units",
    response_model=OrganizationalUnitListResponse,
)
def list_organizational_units(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Kinukuha ang active DICT units kasama ang hierarchy references."""
    organizational_units = db.scalars(
        select(OrganizationalUnit)
        .where(OrganizationalUnit.is_active.is_(True))
        .order_by(OrganizationalUnit.unit_name)
    ).all()

    return success_response(
        organizational_units,
        "Organizational units retrieved.",
    )


@router.post(
    "/organizational-units",
    response_model=CreateOrganizationalUnitResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_unit(
    payload: CreateOrganizationalUnitRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Gumagawa ng active root o child DICT organizational unit."""
    try:
        unit = create_organizational_unit(db, payload)
    except UnitCodeAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "UNIT_CODE_ALREADY_EXISTS",
                "An organizational unit with this code already exists.",
                {"unit_code": "Unit code is already in use."},
            ),
        )
    except InvalidParentUnitError:
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "VALIDATION_ERROR",
                "Some fields are invalid.",
                {"parent_unit_id": "Select an active parent unit."},
            ),
        )

    return success_response(unit, "Organizational unit created.")
