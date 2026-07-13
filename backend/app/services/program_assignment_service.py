"""Business rules para sa Program Admin assignment lifecycle."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import Program, ProgramAdminAssignment, User
from app.schemas.programs import CreateProgramAssignmentRequest


class ProgramNotFoundForAssignmentError(Exception):
    """Raised kapag walang target program."""


class ProgramArchivedError(Exception):
    """Raised kapag archived ang program na bibigyan ng admin."""


class InvalidProgramAdminError(Exception):
    """Raised kapag user ay missing, inactive, o hindi Program Admin."""


class AssignmentAlreadyActiveError(Exception):
    """Raised kapag active na ang same user-program pair."""


class AssignmentNotFoundError(Exception):
    """Raised kapag walang assignment para sa supplied ID."""


@dataclass
class AssignmentResult:
    assignment: ProgramAdminAssignment
    user: User
    created: bool


def _now_without_timezone() -> datetime:
    """MySQL DATETIME is timezone-naive; UTC pa rin ang stored value."""
    return datetime.now(UTC).replace(tzinfo=None)


def _commit_assignment_write(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        # Unique pair constraint ang final protection sa sabay na assignment.
        db.rollback()
        raise AssignmentAlreadyActiveError from exc


def list_program_assignments(
    db: Session,
    program_id: int,
) -> list[ProgramAdminAssignment]:
    if db.get(Program, program_id) is None:
        raise ProgramNotFoundForAssignmentError

    statement = (
        select(ProgramAdminAssignment)
        .options(selectinload(ProgramAdminAssignment.user))
        .where(ProgramAdminAssignment.program_id == program_id)
        .order_by(ProgramAdminAssignment.assigned_at.desc())
    )
    return list(db.scalars(statement).all())


def assign_program_admin(
    db: Session,
    program_id: int,
    payload: CreateProgramAssignmentRequest,
    current_super_admin_id: int,
) -> AssignmentResult:
    program = db.get(Program, program_id)
    if program is None:
        raise ProgramNotFoundForAssignmentError
    if program.program_status != "active":
        raise ProgramArchivedError

    user = db.get(User, payload.user_id)
    if (
        user is None
        or user.account_status != "active"
        or not user.role.is_active
        or user.role.role_name != "program_admin"
    ):
        raise InvalidProgramAdminError

    existing = db.scalar(
        select(ProgramAdminAssignment).where(
            ProgramAdminAssignment.program_id == program_id,
            ProgramAdminAssignment.user_id == payload.user_id,
        )
    )
    if existing is not None:
        if existing.assignment_status == "active":
            raise AssignmentAlreadyActiveError

        # Unique ang pair, kaya nire-reactivate ang row imbes na mag-duplicate.
        existing.assignment_status = "active"
        existing.assigned_by_user_id = current_super_admin_id
        existing.assigned_at = _now_without_timezone()
        existing.revoked_at = None
        _commit_assignment_write(db)
        db.refresh(existing)
        return AssignmentResult(assignment=existing, user=user, created=False)

    assignment = ProgramAdminAssignment(
        program_id=program_id,
        user_id=payload.user_id,
        assigned_by_user_id=current_super_admin_id,
        assignment_status="active",
        revoked_at=None,
    )
    db.add(assignment)
    _commit_assignment_write(db)
    db.refresh(assignment)
    return AssignmentResult(assignment=assignment, user=user, created=True)


def revoke_program_assignment(
    db: Session,
    assignment_id: int,
) -> AssignmentResult:
    assignment = db.get(ProgramAdminAssignment, assignment_id)
    if assignment is None:
        raise AssignmentNotFoundError

    if assignment.assignment_status == "active":
        assignment.assignment_status = "revoked"
        assignment.revoked_at = _now_without_timezone()
        _commit_assignment_write(db)
        db.refresh(assignment)

    return AssignmentResult(
        assignment=assignment,
        user=assignment.user,
        created=False,
    )
