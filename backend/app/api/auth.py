"""Admin authentication routes."""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.config import Settings, get_settings
from app.core.responses import error_response, success_response
from app.core.security import create_access_token
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_admin

router = APIRouter(prefix="/auth", tags=["auth"])


def _current_user_data(user: User) -> dict[str, Any]:
    """Ginagawang frontend-friendly dict ang current admin user."""
    org_unit = None
    if user.org_unit is not None:
        org_unit = {
            "org_unit_id": user.org_unit.org_unit_id,
            "unit_name": user.org_unit.unit_name,
        }

    return {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "account_status": user.account_status,
        "role": {
            "role_id": user.role.role_id,
            "role_name": user.role.role_name,
        },
        "org_unit": org_unit,
    }


@router.post("/login", response_model=None)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any] | JSONResponse:
    """Admin login endpoint for Super Admin and Program Admin users."""
    user = authenticate_admin(db, payload.email, payload.password)
    if user is None:
        return JSONResponse(
            status_code=401,
            content=error_response(
                "INVALID_CREDENTIALS",
                "Invalid email or password.",
            ),
        )

    access_token = create_access_token(str(user.user_id), settings)
    token_response = TokenResponse(
        access_token=access_token,
        expires_in_minutes=settings.jwt_access_token_expire_minutes,
    )

    return success_response(token_response.model_dump(), "Login successful.")


@router.get("/me")
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Returns the currently logged-in admin user."""
    return success_response(
        _current_user_data(current_user),
        "Current user retrieved.",
    )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Stateless logout; frontend ang magtatanggal ng stored token."""
    return success_response(
        {"logged_out": True},
        "Logout successful. Remove the token on the frontend.",
    )
