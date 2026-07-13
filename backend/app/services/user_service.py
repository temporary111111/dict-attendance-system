"""Business rules para sa paggawa at pag-manage ng admin users."""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import OrganizationalUnit, Role, User
from app.schemas.users import CreateUserRequest
from app.services.auth_service import ADMIN_ROLE_NAMES


class UserEmailAlreadyExistsError(Exception):
    """Raised kapag may existing user na gumagamit na ng email."""


class InvalidUserReferenceError(Exception):
    """Raised kapag invalid o inactive ang selected role o unit."""

    def __init__(self, field_name: str, field_message: str):
        super().__init__(field_message)
        self.field_name = field_name
        self.field_message = field_message


@dataclass(frozen=True)
class CreatedAdminUser:
    """Pinagsamang created user at validated reference records."""

    user: User
    role: Role
    org_unit: OrganizationalUnit | None


def create_admin_user(
    db: Session,
    payload: CreateUserRequest,
) -> CreatedAdminUser:
    """Vine-validate ang references at sine-save ang hashed admin account."""
    normalized_email = str(payload.email).strip().lower()
    existing_user_id = db.scalar(
        select(User.user_id).where(func.lower(User.email) == normalized_email)
    )
    if existing_user_id is not None:
        raise UserEmailAlreadyExistsError

    role = db.get(Role, payload.role_id)
    if (
        role is None
        or not role.is_active
        or role.role_name not in ADMIN_ROLE_NAMES
    ):
        raise InvalidUserReferenceError(
            "role_id",
            "Select an active admin role.",
        )

    org_unit = None
    if payload.org_unit_id is not None:
        org_unit = db.get(OrganizationalUnit, payload.org_unit_id)
        if org_unit is None or not org_unit.is_active:
            raise InvalidUserReferenceError(
                "org_unit_id",
                "Select an active organizational unit.",
            )

    user = User(
        role_id=role.role_id,
        org_unit_id=org_unit.org_unit_id if org_unit is not None else None,
        full_name=payload.full_name,
        email=normalized_email,
        password_hash=hash_password(payload.password),
        account_status="active",
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        # Database constraint pa rin ang final protection laban sa race condition.
        db.rollback()
        raise UserEmailAlreadyExistsError from exc

    db.refresh(user)
    return CreatedAdminUser(user=user, role=role, org_unit=org_unit)

