"""Auth business logic para sa admin login."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import User

ADMIN_ROLE_NAMES = {"super_admin", "program_admin"}


def authenticate_admin(db: Session, email: str, password: str) -> User | None:
    """Returns the admin user kapag valid ang login credentials."""
    normalized_email = email.strip().lower()
    result = db.execute(
        select(User)
        .join(User.role)
        .where(func.lower(User.email) == normalized_email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        return None

    # Same generic rejection path para hindi ma-reveal kung email or password ang mali.
    if user.account_status != "active":
        return None

    if user.role.role_name not in ADMIN_ROLE_NAMES or not user.role.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
