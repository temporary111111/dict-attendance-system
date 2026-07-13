"""Super Admin routes para sa Program Admin assignments."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.models import ProgramAdminAssignment, User
from app.schemas.programs import (
    CreateProgramAssignmentRequest,
    ProgramAssignmentListResponse,
    ProgramAssignmentResponse,
)
from app.services.program_assignment_service import (
    AssignmentAlreadyActiveError,
    AssignmentNotFoundError,
    InvalidProgramAdminError,
    ProgramArchivedError,
    ProgramNotFoundForAssignmentError,
    assign_program_admin,
    list_program_assignments,
    revoke_program_assignment,
)

router = APIRouter(tags=["program admin assignments"])


def _assignment_data(
    assignment: ProgramAdminAssignment,
    user: User | None = None,
) -> dict[str, Any]:
    assigned_user = user or assignment.user
    return {
        "assignment_id": assignment.assignment_id,
        "program_id": assignment.program_id,
        "user": {
            "user_id": assigned_user.user_id,
            "full_name": assigned_user.full_name,
            "email": assigned_user.email,
        },
        "assigned_by_user_id": assignment.assigned_by_user_id,
        "assignment_status": assignment.assignment_status,
        "assigned_at": assignment.assigned_at,
        "revoked_at": assignment.revoked_at,
    }


def _raise_assignment_error(exc: Exception) -> None:
    if isinstance(exc, ProgramNotFoundForAssignmentError):
        raise HTTPException(
            status_code=404,
            detail=error_response("PROGRAM_NOT_FOUND", "Program not found."),
        )
    if isinstance(exc, ProgramArchivedError):
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "PROGRAM_ARCHIVED",
                "Program Admins cannot be assigned to an archived program.",
            ),
        )
    if isinstance(exc, InvalidProgramAdminError):
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "VALIDATION_ERROR",
                "Some fields are invalid.",
                {"user_id": "Select an active Program Admin account."},
            ),
        )
    if isinstance(exc, AssignmentAlreadyActiveError):
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "ASSIGNMENT_ALREADY_ACTIVE",
                "This Program Admin is already assigned to the program.",
            ),
        )
    if isinstance(exc, AssignmentNotFoundError):
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "ASSIGNMENT_NOT_FOUND",
                "Program Admin assignment not found.",
            ),
        )


@router.get(
    "/programs/{program_id}/admins",
    response_model=ProgramAssignmentListResponse,
)
def list_program_admins(
    program_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_super_admin: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        assignments = list_program_assignments(db, program_id)
    except ProgramNotFoundForAssignmentError as exc:
        _raise_assignment_error(exc)
    return success_response(
        [_assignment_data(assignment) for assignment in assignments],
        "Program Admin assignments retrieved.",
    )


@router.post(
    "/programs/{program_id}/admins",
    response_model=ProgramAssignmentResponse,
    responses={status.HTTP_201_CREATED: {"model": ProgramAssignmentResponse}},
)
def assign_program_admin_record(
    program_id: Annotated[int, Path(gt=0)],
    payload: CreateProgramAssignmentRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    current_super_admin: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        result = assign_program_admin(
            db,
            program_id,
            payload,
            current_super_admin.user_id,
        )
    except (
        AssignmentAlreadyActiveError,
        InvalidProgramAdminError,
        ProgramArchivedError,
        ProgramNotFoundForAssignmentError,
    ) as exc:
        _raise_assignment_error(exc)

    if result.created:
        response.status_code = status.HTTP_201_CREATED
    return success_response(
        _assignment_data(result.assignment, result.user),
        "Program Admin assigned.",
    )


@router.patch(
    "/program-admin-assignments/{assignment_id}/revoke",
    response_model=ProgramAssignmentResponse,
)
def revoke_program_admin_record(
    assignment_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_super_admin: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        result = revoke_program_assignment(db, assignment_id)
    except AssignmentNotFoundError as exc:
        _raise_assignment_error(exc)
    return success_response(
        _assignment_data(result.assignment, result.user),
        "Program Admin assignment revoked.",
    )
