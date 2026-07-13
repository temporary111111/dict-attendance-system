"""Business rules para sa paggawa at pag-manage ng admin users."""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import OrganizationalUnit, Role, User
from app.schemas.users import CreateUserRequest, UpdateUserRequest
from app.services.auth_service import ADMIN_ROLE_NAMES


class UserEmailAlreadyExistsError(Exception):
    """Raised kapag may existing user na gumagamit na ng email."""


class InvalidUserReferenceError(Exception):
    """Raised kapag invalid o inactive ang selected role o unit."""

    def __init__(self, field_name: str, field_message: str):
        super().__init__(field_message)
        self.field_name = field_name
        self.field_message = field_message


class UserNotFoundError(Exception):
    """Raised kapag walang admin user para sa requested ID."""


@dataclass(frozen=True)
class AdminUserResult:
    """Pinagsamang saved user at validated reference records."""

    user: User
    role: Role
    org_unit: OrganizationalUnit | None


def _email_is_in_use(
    db: Session,
    email: str,
    *,
    exclude_user_id: int | None = None,
) -> bool:
    """Case-insensitive duplicate check, optional ang current user exclusion."""
    statement = select(User.user_id).where(func.lower(User.email) == email)
    if exclude_user_id is not None:
        statement = statement.where(User.user_id != exclude_user_id)
    return db.scalar(statement) is not None


def _get_active_admin_role(db: Session, role_id: int) -> Role:
    role = db.get(Role, role_id)
    if (
        role is None
        or not role.is_active
        or role.role_name not in ADMIN_ROLE_NAMES
    ):
        raise InvalidUserReferenceError(
            "role_id",
            "Select an active admin role.",
        )
    return role


def _get_active_org_unit(
    db: Session,
    org_unit_id: int,
) -> OrganizationalUnit:
    org_unit = db.get(OrganizationalUnit, org_unit_id)
    if org_unit is None or not org_unit.is_active:
        raise InvalidUserReferenceError(
            "org_unit_id",
            "Select an active organizational unit.",
        )
    return org_unit


def _commit_user(db: Session) -> None:
    """Commits one user write with DB-level duplicate-email protection."""
    try:
        db.commit()
    except IntegrityError as exc:
        # Database constraint pa rin ang final protection laban sa race condition.
        db.rollback()
        raise UserEmailAlreadyExistsError from exc


def create_admin_user(
    db: Session,
    payload: CreateUserRequest,
) -> AdminUserResult:
    """Vine-validate ang references at sine-save ang hashed admin account."""
    normalized_email = str(payload.email).strip().lower()
    if _email_is_in_use(db, normalized_email):
        raise UserEmailAlreadyExistsError

    role = _get_active_admin_role(db, payload.role_id)

    org_unit = None
    if payload.org_unit_id is not None:
        org_unit = _get_active_org_unit(db, payload.org_unit_id)

    user = User(
        role_id=role.role_id,
        org_unit_id=org_unit.org_unit_id if org_unit is not None else None,
        full_name=payload.full_name,
        email=normalized_email,
        password_hash=hash_password(payload.password),
        account_status="active",
    )
    db.add(user)
    _commit_user(db)
    db.refresh(user)
    return AdminUserResult(user=user, role=role, org_unit=org_unit)


def update_admin_user(
    db: Session,
    user_id: int,
    payload: UpdateUserRequest,
) -> AdminUserResult:
    """Ina-apply lang ang supplied profile fields at sine-save ang user."""
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError

    role = user.role
    org_unit = user.org_unit
    supplied_fields = payload.model_fields_set

    if "full_name" in supplied_fields:
        user.full_name = payload.full_name

    if "email" in supplied_fields:
        normalized_email = str(payload.email).strip().lower()
        if _email_is_in_use(
            db,
            normalized_email,
            exclude_user_id=user_id,
        ):
            raise UserEmailAlreadyExistsError
        user.email = normalized_email

    if "role_id" in supplied_fields:
        role = _get_active_admin_role(db, payload.role_id)
        user.role_id = role.role_id

    if "org_unit_id" in supplied_fields:
        if payload.org_unit_id is None:
            org_unit = None
            user.org_unit_id = None
        else:
            org_unit = _get_active_org_unit(db, payload.org_unit_id)
            user.org_unit_id = org_unit.org_unit_id

    _commit_user(db)
    db.refresh(user)
    return AdminUserResult(user=user, role=role, org_unit=org_unit)
