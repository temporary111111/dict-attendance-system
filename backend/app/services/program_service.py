"""Business rules para sa DICT program records at admin visibility."""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import OrganizationalUnit, Program, ProgramAdminAssignment, User
from app.schemas.programs import (
    ChangeProgramStatusRequest,
    CreateProgramRequest,
    UpdateProgramRequest,
)


class ProgramNotFoundError(Exception):
    """Raised kapag walang program para sa supplied ID."""


class ProgramAccessDeniedError(Exception):
    """Raised kapag hindi assigned ang Program Admin sa program."""


class InvalidOwningUnitError(Exception):
    """Raised kapag missing o inactive ang program owner unit."""


class ProgramNameAlreadyExistsError(Exception):
    """Raised kapag duplicate ang program name sa same owning unit."""


@dataclass
class ProgramResult:
    program: Program
    owning_unit: OrganizationalUnit


def _get_active_owning_unit(
    db: Session,
    owning_unit_id: int,
) -> OrganizationalUnit:
    owning_unit = db.get(OrganizationalUnit, owning_unit_id)
    if owning_unit is None or not owning_unit.is_active:
        raise InvalidOwningUnitError
    return owning_unit


def _program_name_is_in_use(
    db: Session,
    owning_unit_id: int,
    program_name: str,
    *,
    exclude_program_id: int | None = None,
) -> bool:
    statement = select(Program.program_id).where(
        Program.owning_unit_id == owning_unit_id,
        func.lower(Program.program_name) == program_name.lower(),
    )
    if exclude_program_id is not None:
        statement = statement.where(Program.program_id != exclude_program_id)
    return db.scalar(statement) is not None


def _commit_program_write(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        # DB unique constraint ang final protection kapag sabay ang requests.
        db.rollback()
        raise ProgramNameAlreadyExistsError from exc


def list_visible_programs(db: Session, current_user: User) -> list[Program]:
    """Super Admin sees all; Program Admin sees active assignments only."""
    statement = select(Program).options(selectinload(Program.owning_unit))
    if current_user.role.role_name == "program_admin":
        statement = statement.join(ProgramAdminAssignment).where(
            ProgramAdminAssignment.user_id == current_user.user_id,
            ProgramAdminAssignment.assignment_status == "active",
        )
    statement = statement.order_by(Program.program_name)
    return list(db.scalars(statement).all())


def get_visible_program(
    db: Session,
    program_id: int,
    current_user: User,
) -> Program:
    program = db.get(Program, program_id)
    if program is None:
        raise ProgramNotFoundError

    if current_user.role.role_name == "program_admin":
        assignment_id = db.scalar(
            select(ProgramAdminAssignment.assignment_id).where(
                ProgramAdminAssignment.program_id == program_id,
                ProgramAdminAssignment.user_id == current_user.user_id,
                ProgramAdminAssignment.assignment_status == "active",
            )
        )
        if assignment_id is None:
            raise ProgramAccessDeniedError

    return program


def create_program(
    db: Session,
    payload: CreateProgramRequest,
    current_super_admin_id: int,
) -> ProgramResult:
    owning_unit = _get_active_owning_unit(db, payload.owning_unit_id)
    if _program_name_is_in_use(
        db,
        payload.owning_unit_id,
        payload.program_name,
    ):
        raise ProgramNameAlreadyExistsError

    program = Program(
        owning_unit_id=payload.owning_unit_id,
        created_by_user_id=current_super_admin_id,
        program_name=payload.program_name,
        description=payload.description,
        program_status="active",
    )
    db.add(program)
    _commit_program_write(db)
    db.refresh(program)
    return ProgramResult(program=program, owning_unit=owning_unit)


def update_program(
    db: Session,
    program_id: int,
    payload: UpdateProgramRequest,
) -> ProgramResult:
    program = db.get(Program, program_id)
    if program is None:
        raise ProgramNotFoundError

    supplied_fields = payload.model_fields_set
    owning_unit = program.owning_unit
    target_unit_id = program.owning_unit_id
    target_name = program.program_name

    if "owning_unit_id" in supplied_fields:
        target_unit_id = payload.owning_unit_id
        owning_unit = _get_active_owning_unit(db, target_unit_id)
    if "program_name" in supplied_fields:
        target_name = payload.program_name

    if _program_name_is_in_use(
        db,
        target_unit_id,
        target_name,
        exclude_program_id=program_id,
    ):
        raise ProgramNameAlreadyExistsError

    if "owning_unit_id" in supplied_fields:
        program.owning_unit_id = target_unit_id
    if "program_name" in supplied_fields:
        program.program_name = target_name
    if "description" in supplied_fields:
        program.description = payload.description

    _commit_program_write(db)
    db.refresh(program)
    return ProgramResult(program=program, owning_unit=owning_unit)


def change_program_status(
    db: Session,
    program_id: int,
    payload: ChangeProgramStatusRequest,
) -> ProgramResult:
    program = db.get(Program, program_id)
    if program is None:
        raise ProgramNotFoundError

    owning_unit = program.owning_unit
    if payload.program_status == "active":
        owning_unit = _get_active_owning_unit(db, program.owning_unit_id)

    program.program_status = payload.program_status
    _commit_program_write(db)
    db.refresh(program)
    return ProgramResult(program=program, owning_unit=owning_unit)
