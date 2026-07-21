"""Role-aware program read routes at Super Admin program management routes."""

from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_super_admin
from app.core.config import Settings, get_settings
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
from app.services.program_logo_service import (
    InvalidProgramLogoError,
    delete_program_logo,
    save_program_logo,
)
from app.services.program_service import (
    InvalidOwningUnitError,
    ProgramAccessDeniedError,
    ProgramNameAlreadyExistsError,
    ProgramHasOpenEventsError,
    ProgramNotFoundError,
    change_program_status,
    create_program,
    get_visible_program,
    list_visible_programs,
    update_program,
)

router = APIRouter(prefix="/programs", tags=["programs"])


def _logo_url(program: Program, settings: Settings) -> str | None:
    """Ginagawang full media URL ang stored logo filename."""
    if not program.logo_path:
        return None
    return f"{settings.program_logo_url_prefix}/{program.logo_path}"


def _program_data(
    program: Program,
    settings: Settings,
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
        "logo_url": _logo_url(program, settings),
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
    if isinstance(exc, ProgramHasOpenEventsError):
        raise HTTPException(
            status_code=409,
            detail=error_response(
                "PROGRAM_HAS_OPEN_EVENTS",
                "Close all open events before archiving the program.",
            ),
        )


@router.get("", response_model=ProgramListResponse)
def list_programs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    programs = list_visible_programs(db, current_user)
    return success_response(
        [_program_data(program, settings) for program in programs],
        "Programs retrieved.",
    )


@router.post("", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program_record(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_super_admin: Annotated[User, Depends(require_super_admin)],
    settings: Annotated[Settings, Depends(get_settings)],
    program_name: Annotated[str | None, Form()] = None,
    owning_unit_id: Annotated[int | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    logo: Annotated[UploadFile | None, File()] = None,
) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    p_name = program_name
    unit_id = owning_unit_id
    desc = description
    logo_file = logo

    if "application/json" in content_type:
        try:
            body = await request.json()
            p_name = body.get("program_name")
            unit_id = body.get("owning_unit_id")
            desc = body.get("description")
            logo_file = None
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=error_response("VALIDATION_ERROR", str(exc)),
            )

    try:
        payload = CreateProgramRequest(
            program_name=p_name,
            owning_unit_id=unit_id,
            description=desc or None,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "VALIDATION_ERROR",
                "Some fields are invalid.",
                {"owning_unit_id": "Select an active organizational unit."} if "owning_unit" in str(exc) else {}
            ),
        )

    # Save logo file before DB write so we can roll back if DB fails.
    logo_filename: str | None = None
    has_logo = logo_file is not None and bool(logo_file.filename)
    if has_logo:
        try:
            logo_filename = save_program_logo(
                logo_file,
                settings.program_logo_directory,
                settings.program_logo_max_bytes,
            )
        except InvalidProgramLogoError as exc:
            raise HTTPException(
                status_code=422,
                detail=error_response(
                    "INVALID_PROGRAM_LOGO",
                    str(exc),
                    {"logo": str(exc)},
                ),
            )

    try:
        created = create_program(
            db,
            payload,
            current_super_admin.user_id,
            logo_filename=logo_filename,
        )
    except (InvalidOwningUnitError, ProgramNameAlreadyExistsError) as exc:
        # Roll back the saved logo file on DB error.
        delete_program_logo(settings.program_logo_directory, logo_filename)
        _raise_program_write_error(exc)

    return success_response(
        _program_data(created.program, settings, created.owning_unit),
        "Program created.",
    )


@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(
    program_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
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
    return success_response(_program_data(program, settings), "Program retrieved.")


@router.patch("/{program_id}", response_model=ProgramResponse)
async def update_program_record(
    program_id: Annotated[int, Path(gt=0)],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_super_admin: Annotated[User, Depends(require_super_admin)],
    settings: Annotated[Settings, Depends(get_settings)],
    program_name: Annotated[str | None, Form()] = None,
    owning_unit_id: Annotated[int | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    remove_logo: Annotated[bool, Form()] = False,
    logo: Annotated[UploadFile | None, File()] = None,
) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    p_name = program_name
    unit_id = owning_unit_id
    desc = description
    logo_file = logo
    rem_logo = remove_logo

    raw: dict[str, Any] = {}
    if "application/json" in content_type:
        try:
            body = await request.json()
            if "program_name" in body:
                raw["program_name"] = body["program_name"]
            if "owning_unit_id" in body:
                raw["owning_unit_id"] = body["owning_unit_id"]
            if "description" in body:
                raw["description"] = body["description"]
            logo_file = None
            rem_logo = False
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=error_response("VALIDATION_ERROR", str(exc)),
            )
    else:
        if p_name is not None:
            raw["program_name"] = p_name
        if unit_id is not None:
            raw["owning_unit_id"] = unit_id
        if desc is not None:
            raw["description"] = desc

    try:
        payload = UpdateProgramRequest.model_validate(raw)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=error_response("VALIDATION_ERROR", str(exc)),
        )

    # Fetch program to get the old logo path for cleanup.
    program = db.get(Program, program_id)
    if program is None:
        raise HTTPException(
            status_code=404,
            detail=error_response("PROGRAM_NOT_FOUND", "Program not found."),
        )
    old_logo_filename = program.logo_path

    has_logo = logo_file is not None and bool(logo_file.filename)
    new_logo_filename: str | None = None
    if has_logo:
        try:
            new_logo_filename = save_program_logo(
                logo_file,
                settings.program_logo_directory,
                settings.program_logo_max_bytes,
            )
        except InvalidProgramLogoError as exc:
            raise HTTPException(
                status_code=422,
                detail=error_response(
                    "INVALID_PROGRAM_LOGO",
                    str(exc),
                    {"logo": str(exc)},
                ),
            )

    try:
        updated = update_program(
            db,
            program_id,
            payload,
            logo_filename=new_logo_filename,
            remove_logo=rem_logo,
        )
    except (
        InvalidOwningUnitError,
        ProgramNameAlreadyExistsError,
        ProgramNotFoundError,
    ) as exc:
        delete_program_logo(settings.program_logo_directory, new_logo_filename)
        _raise_program_write_error(exc)

    # Delete the old logo file after a successful DB update.
    if new_logo_filename is not None or rem_logo:
        delete_program_logo(settings.program_logo_directory, old_logo_filename)

    return success_response(
        _program_data(updated.program, settings, updated.owning_unit),
        "Program updated.",
    )


@router.patch("/{program_id}/archive", response_model=ProgramResponse)
def archive_or_restore_program(
    program_id: Annotated[int, Path(gt=0)],
    payload: ChangeProgramStatusRequest,
    db: Annotated[Session, Depends(get_db)],
    current_super_admin: Annotated[User, Depends(require_super_admin)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    try:
        updated = change_program_status(db, program_id, payload)
    except (
        InvalidOwningUnitError,
        ProgramHasOpenEventsError,
        ProgramNotFoundError,
    ) as exc:
        _raise_program_write_error(exc)
    return success_response(
        _program_data(updated.program, settings, updated.owning_unit),
        "Program status updated.",
    )
