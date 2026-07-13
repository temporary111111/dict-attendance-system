"""Super Admin routes para sa admin user accounts."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.schemas.users import CreateUserRequest, CreateUserResponse
from app.services.user_service import (
    CreatedAdminUser,
    InvalidUserReferenceError,
    UserEmailAlreadyExistsError,
    create_admin_user,
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_super_admin)],
)


def _created_user_data(created: CreatedAdminUser) -> dict[str, Any]:
    """Inaalis ang password hash at binabalik lang ang safe account fields."""
    org_unit = None
    if created.org_unit is not None:
        org_unit = {
            "org_unit_id": created.org_unit.org_unit_id,
            "unit_name": created.org_unit.unit_name,
        }

    return {
        "user_id": created.user.user_id,
        "full_name": created.user.full_name,
        "email": created.user.email,
        "account_status": created.user.account_status,
        "role": {
            "role_id": created.role.role_id,
            "role_name": created.role.role_name,
        },
        "org_unit": org_unit,
    }


@router.post("", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Gumagawa ng active Super Admin o Program Admin account."""
    try:
        created = create_admin_user(db, payload)
    except UserEmailAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "EMAIL_ALREADY_EXISTS",
                "An admin user with this email already exists.",
                {"email": "Email is already in use."},
            ),
        )
    except InvalidUserReferenceError as exc:
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "VALIDATION_ERROR",
                "Some fields are invalid.",
                {exc.field_name: exc.field_message},
            ),
        )

    return success_response(
        _created_user_data(created),
        "Admin user created.",
    )

