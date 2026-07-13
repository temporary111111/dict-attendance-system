"""Role-aware program read routes at Super Admin program management routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_super_admin
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.models import OrganizationalUnit, Program, User
from app.schemas.programs import (
    ChangeProgramStatusRequest,
    CreateProgramRequest,
    ProgramListResponse,
    ProgramResponse,
    UpdateProgramRequest,
)
from app.services.program_service import (
    InvalidOwningUnitError,
    ProgramAccessDeniedError,
    ProgramNameAlreadyExistsError,
    ProgramNotFoundError,
    change_program_status,
    create_program,
    get_visible_program,
    list_visible_programs,
    update_program,
)

router = APIRouter(prefix="/programs", tags=["programs"])


def _program_data(
    program: Program,
    owning_unit: OrganizationalUnit | None = None,
) -> dict[str, Any]:
    unit = owning_unit or program.owning_unit
    return {
        "program_id": program.program_id,
        "owning_unit": {
            "org_unit_id": unit.org_unit_id,
            "unit_name": unit.unit_name,
        },
        "created_by_user_id": program.created_by_user_id,
        "program_name": program.program_name,
        "description": program.description,
        "program_status": program.program_status,
    }


def _raise_program_write_error(exc: Exception) -> None:
    if isinstance(exc, ProgramNotFoundError):
        raise HTTPException(
            status_code=404,
            detail=error_response("PROGRAM_NOT_FOUND", "Program not found."),
        )
    if isinstance(exc, ProgramNameAlreadyExistsError):
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "PROGRAM_NAME_ALREADY_EXISTS",
                "A program with this name already exists in the owning unit.",
                {"program_name": "Program name is already in use."},
            ),
        )
    if isinstance(exc, InvalidOwningUnitError):
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "VALIDATION_ERROR",
                "Some fields are invalid.",
                {"owning_unit_id": "Select an active organizational unit."},
            ),
        )


@router.get("", response_model=ProgramListResponse)
def list_programs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    programs = list_visible_programs(db, current_user)
    return success_response(
        [_program_data(program) for program in programs],
        "Programs retrieved.",
    )


@router.post("", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
def create_program_record(
    payload: CreateProgramRequest,
    db: Annotated[Session, Depends(get_db)],
    current_super_admin: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        created = create_program(db, payload, current_super_admin.user_id)
    except (InvalidOwningUnitError, ProgramNameAlreadyExistsError) as exc:
        _raise_program_write_error(exc)
    return success_response(
        _program_data(created.program, created.owning_unit),
        "Program created.",
    )


@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(
    program_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    try:
        program = get_visible_program(db, program_id, current_user)
    except ProgramNotFoundError as exc:
        _raise_program_write_error(exc)
    except ProgramAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail=error_response(
                "FORBIDDEN",
                "You are not assigned to this program.",
            ),
        )
    return success_response(_program_data(program), "Program retrieved.")


@router.patch("/{program_id}", response_model=ProgramResponse)
def update_program_record(
    program_id: Annotated[int, Path(gt=0)],
    payload: UpdateProgramRequest,
    db: Annotated[Session, Depends(get_db)],
    current_super_admin: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        updated = update_program(db, program_id, payload)
    except (
        InvalidOwningUnitError,
        ProgramNameAlreadyExistsError,
        ProgramNotFoundError,
    ) as exc:
        _raise_program_write_error(exc)
    return success_response(
        _program_data(updated.program, updated.owning_unit),
        "Program updated.",
    )


@router.patch("/{program_id}/archive", response_model=ProgramResponse)
def archive_or_restore_program(
    program_id: Annotated[int, Path(gt=0)],
    payload: ChangeProgramStatusRequest,
    db: Annotated[Session, Depends(get_db)],
    current_super_admin: Annotated[User, Depends(require_super_admin)],
) -> dict[str, Any]:
    try:
        updated = change_program_status(db, program_id, payload)
    except (InvalidOwningUnitError, ProgramNotFoundError) as exc:
        _raise_program_write_error(exc)
    return success_response(
        _program_data(updated.program, updated.owning_unit),
        "Program status updated.",
    )
