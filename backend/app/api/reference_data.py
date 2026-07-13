"""Read-only reference data na ginagamit sa admin account management."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.core.responses import success_response
from app.db.session import get_db
from app.models import OrganizationalUnit, Role
from app.schemas.reference_data import (
    OrganizationalUnitListResponse,
    RoleListResponse,
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

