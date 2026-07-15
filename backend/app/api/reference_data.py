"""Reference data at organizational unit management routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
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
    UpdateOrganizationalUnitRequest,
    UpdateOrganizationalUnitResponse,
)
from app.services.organizational_unit_service import (
    CircularUnitHierarchyError,
    InvalidParentUnitError,
    OrganizationalUnitNotFoundError,
    UnitCodeAlreadyExistsError,
    UnitHasActiveChildrenError,
    create_organizational_unit,
    update_organizational_unit,
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
    include_inactive: Annotated[bool, Query(alias="includeInactive")] = False,
) -> dict[str, Any]:
    """Kinukuha ang DICT units kasama ang hierarchy at status."""
    statement = select(OrganizationalUnit)
    if not include_inactive:
        statement = statement.where(OrganizationalUnit.is_active.is_(True))
    organizational_units = db.scalars(
        statement.order_by(OrganizationalUnit.unit_name)
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


@router.patch(
    "/organizational-units/{org_unit_id}",
    response_model=UpdateOrganizationalUnitResponse,
)
def update_unit(
    org_unit_id: Annotated[int, Path(gt=0)],
    payload: UpdateOrganizationalUnitRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Ina-update ang supplied unit fields nang pinoprotektahan ang hierarchy."""
    try:
        unit = update_organizational_unit(db, org_unit_id, payload)
    except OrganizationalUnitNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "ORGANIZATIONAL_UNIT_NOT_FOUND",
                "Organizational unit was not found.",
            ),
        )
    except UnitCodeAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "UNIT_CODE_ALREADY_EXISTS",
                "An organizational unit with this code already exists.",
                {"unit_code": "Unit code is already in use."},
            ),
        )
    except UnitHasActiveChildrenError:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "UNIT_HAS_ACTIVE_CHILDREN",
                "Deactivate the active child units first.",
            ),
        )
    except (InvalidParentUnitError, CircularUnitHierarchyError):
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "VALIDATION_ERROR",
                "Some fields are invalid.",
                {
                    "parent_unit_id": (
                        "Select an active parent outside this unit's children."
                    )
                },
            ),
        )

    return success_response(unit, "Organizational unit updated.")
