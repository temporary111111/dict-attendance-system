"""Creates or updates the local Super Admin account.

Gamitin ito sa local setup para hindi mag-store ng plain password sa SQL files.
"""

from __future__ import annotations

import argparse
import getpass
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import OrganizationalUnit, Role, User


class AdminSetupError(RuntimeError):
    """Raised kapag kulang ang seed data or invalid ang setup input."""


@dataclass(frozen=True)
class AdminSetupResult:
    """Result ng admin setup command para malinaw kung create or update."""

    user: User
    created: bool


def _find_role(db: Session, role_name: str) -> Role | None:
    result = db.execute(
        select(Role).where(Role.role_name == role_name, Role.is_active == 1)
    )
    return result.scalar_one_or_none()


def _find_org_unit(db: Session, unit_code: str) -> OrganizationalUnit | None:
    result = db.execute(
        select(OrganizationalUnit).where(
            OrganizationalUnit.unit_code == unit_code,
            OrganizationalUnit.is_active == 1,
        )
    )
    return result.scalar_one_or_none()


def _find_user_by_email(db: Session, email: str) -> User | None:
    result = db.execute(select(User).where(func.lower(User.email) == email))
    return result.scalar_one_or_none()


def create_or_update_super_admin(
    db: Session,
    full_name: str,
    email: str,
    password: str,
    org_unit_code: str = "DICT",
) -> AdminSetupResult:
    """Creates or updates one active Super Admin using a hashed password."""
    normalized_email = email.strip().lower()
    clean_full_name = full_name.strip()

    if not clean_full_name:
        raise AdminSetupError("Full name is required.")
    if not normalized_email:
        raise AdminSetupError("Email is required.")
    if len(password) < 8:
        raise AdminSetupError("Password must be at least 8 characters.")

    role = _find_role(db, "super_admin")
    if role is None:
        raise AdminSetupError("Missing active super_admin role. Run seed-core.sql first.")

    org_unit = _find_org_unit(db, org_unit_code)
    if org_unit is None:
        raise AdminSetupError(f"Missing active {org_unit_code} org unit. Run seed-core.sql first.")

    password_hash = hash_password(password)
    user = _find_user_by_email(db, normalized_email)

    if user is None:
        user = User(
            role_id=role.role_id,
            org_unit_id=org_unit.org_unit_id,
            full_name=clean_full_name,
            email=normalized_email,
            password_hash=password_hash,
            account_status="active",
        )
        db.add(user)
        created = True
    else:
        # Existing email gets promoted/updated for local setup convenience.
        user.role_id = role.role_id
        user.org_unit_id = org_unit.org_unit_id
        user.full_name = clean_full_name
        user.password_hash = password_hash
        user.account_status = "active"
        created = False

    db.commit()
    db.refresh(user)

    return AdminSetupResult(user=user, created=created)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update a local Super Admin user.",
    )
    parser.add_argument("--email", required=True, help="Super Admin email address.")
    parser.add_argument("--full-name", required=True, help="Super Admin full name.")
    parser.add_argument(
        "--org-unit-code",
        default="DICT",
        help="Organizational unit code to assign. Default: DICT.",
    )
    return parser.parse_args()


def prompt_password() -> str:
    """Hidden password prompt para hindi lumabas ang password sa terminal."""
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if password != confirm_password:
        raise AdminSetupError("Passwords do not match.")

    return password


def main() -> None:
    args = parse_args()

    try:
        password = prompt_password()
        with SessionLocal() as db:
            result = create_or_update_super_admin(
                db,
                full_name=args.full_name,
                email=args.email,
                password=password,
                org_unit_code=args.org_unit_code,
            )
    except AdminSetupError as exc:
        raise SystemExit(f"Admin setup failed: {exc}") from exc

    action = "Created" if result.created else "Updated"
    print(f"{action} Super Admin user: {result.user.email}")


if __name__ == "__main__":
    main()
