"""Super Admin routes para sa admin user accounts."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies.auth import require_super_admin
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.models import User
from app.schemas.users import (
    CreateUserRequest,
    CreateUserResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    UserDetailResponse,
    UserListResponse,
)
from app.services.user_service import (
    AdminUserResult,
    InvalidUserReferenceError,
    UserEmailAlreadyExistsError,
    UserNotFoundError,
    create_admin_user,
    update_admin_user,
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_super_admin)],
)


def _admin_user_data(
    user: User,
    role: Any,
    org_unit_record: Any | None,
) -> dict[str, Any]:
    """Inaalis ang password hash at binabalik lang ang safe account fields."""
    org_unit = None
    if org_unit_record is not None:
        org_unit = {
            "org_unit_id": org_unit_record.org_unit_id,
            "unit_name": org_unit_record.unit_name,
        }

    return {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "account_status": user.account_status,
        "role": {
            "role_id": role.role_id,
            "role_name": role.role_name,
        },
        "org_unit": org_unit,
    }


def _raise_user_write_error(exc: Exception) -> None:
    """Iisang HTTP mapping para pareho ang create at update errors."""
    if isinstance(exc, UserEmailAlreadyExistsError):
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "EMAIL_ALREADY_EXISTS",
                "An admin user with this email already exists.",
                {"email": "Email is already in use."},
            ),
        )

    if isinstance(exc, InvalidUserReferenceError):
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "VALIDATION_ERROR",
                "Some fields are invalid.",
                {exc.field_name: exc.field_message},
            ),
        )

    if isinstance(exc, UserNotFoundError):
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "USER_NOT_FOUND",
                "Admin user not found.",
            ),
        )

    raise exc


@router.get("", response_model=UserListResponse)
def list_users(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Nililista ang active at inactive admin accounts para ma-manage sila."""
    users = db.scalars(
        select(User)
        .options(
            joinedload(User.role),
            joinedload(User.org_unit),
        )
        .order_by(User.full_name, User.user_id)
    ).all()

    return success_response(
        [
            _admin_user_data(user, user.role, user.org_unit)
            for user in users
        ],
        "Admin users retrieved.",
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Kinukuha ang isang admin account gamit ang user ID."""
    user = db.scalar(
        select(User)
        .options(
            joinedload(User.role),
            joinedload(User.org_unit),
        )
        .where(User.user_id == user_id)
    )
    if user is None:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "USER_NOT_FOUND",
                "Admin user not found.",
            ),
        )

    return success_response(
        _admin_user_data(user, user.role, user.org_unit),
        "Admin user retrieved.",
    )


@router.patch("/{user_id}", response_model=UpdateUserResponse)
def update_user(
    user_id: Annotated[int, Path(gt=0)],
    payload: UpdateUserRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Ina-update ang supplied admin profile fields maliban sa status/password."""
    try:
        updated = update_admin_user(db, user_id, payload)
    except (
        UserEmailAlreadyExistsError,
        InvalidUserReferenceError,
        UserNotFoundError,
    ) as exc:
        _raise_user_write_error(exc)

    return success_response(
        _admin_user_data(updated.user, updated.role, updated.org_unit),
        "Admin user updated.",
    )


@router.post("", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Gumagawa ng active Super Admin o Program Admin account."""
    try:
        created = create_admin_user(db, payload)
    except (UserEmailAlreadyExistsError, InvalidUserReferenceError) as exc:
        _raise_user_write_error(exc)

    return success_response(
        _admin_user_data(created.user, created.role, created.org_unit),
        "Admin user created.",
    )
