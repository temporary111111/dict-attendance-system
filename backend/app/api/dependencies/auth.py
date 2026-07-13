"""Auth dependencies para sa current user at role checks."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.responses import error_response
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.services.auth_service import ADMIN_ROLE_NAMES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _raise_auth_error(status_code: int, code: str, message: str) -> None:
    raise HTTPException(
        status_code=status_code,
        detail=error_response(code, message),
    )


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Binabasa ang Bearer token at hinahanap ang active admin user sa DB."""
    if not token:
        _raise_auth_error(
            401,
            "NOT_AUTHENTICATED",
            "Authentication token is required.",
        )

    try:
        payload = decode_access_token(token, settings)
    except jwt.ExpiredSignatureError:
        _raise_auth_error(401, "TOKEN_EXPIRED", "Authentication token has expired.")
    except jwt.InvalidTokenError:
        _raise_auth_error(401, "INVALID_TOKEN", "Authentication token is invalid.")

    subject = payload.get("sub")
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        _raise_auth_error(401, "INVALID_TOKEN", "Authentication token is invalid.")

    user = db.get(User, user_id)
    if user is None:
        _raise_auth_error(401, "INVALID_TOKEN", "Authentication token is invalid.")

    # Token valid pa rin dapat i-check sa DB para inactive users hindi makapasok.
    if user.account_status != "active":
        _raise_auth_error(401, "ACCOUNT_INACTIVE", "User account is inactive.")

    if user.role.role_name not in ADMIN_ROLE_NAMES or not user.role.is_active:
        _raise_auth_error(403, "FORBIDDEN", "User role is not allowed.")

    return user


def require_super_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Allows only Super Admin users."""
    if current_user.role.role_name != "super_admin":
        _raise_auth_error(403, "FORBIDDEN", "Super Admin access is required.")
    return current_user


def require_program_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Allows only Program Admin users."""
    if current_user.role.role_name != "program_admin":
        _raise_auth_error(403, "FORBIDDEN", "Program Admin access is required.")
    return current_user
