"""Request at response schemas para sa programs at admin assignments."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

TrimmedProgramName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]
TrimmedProgramDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=5000),
]


class OrganizationalUnitSummary(BaseModel):
    org_unit_id: int
    unit_name: str


class ProgramData(BaseModel):
    program_id: int
    owning_unit: OrganizationalUnitSummary
    created_by_user_id: int
    program_name: str
    description: str | None
    logo_url: str | None
    program_status: Literal["active", "archived"]


class ProgramListResponse(BaseModel):
    data: list[ProgramData]
    message: str


class ProgramResponse(BaseModel):
    data: ProgramData
    message: str


class CreateProgramRequest(BaseModel):
    """Required fields kapag gumagawa ang Super Admin ng program."""

    owning_unit_id: int = Field(gt=0)
    program_name: TrimmedProgramName
    description: TrimmedProgramDescription | None = None


class UpdateProgramRequest(BaseModel):
    """Optional fields para sa partial program update."""

    owning_unit_id: int | None = Field(default=None, gt=0)
    program_name: TrimmedProgramName | None = None
    description: TrimmedProgramDescription | None = None

    @field_validator("owning_unit_id", "program_name")
    @classmethod
    def reject_null_required_values(cls, value, info):
        if value is None:
            raise ValueError(f"{info.field_name} cannot be null.")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        return self


class ChangeProgramStatusRequest(BaseModel):
    program_status: Literal["active", "archived"]


class CreateProgramAssignmentRequest(BaseModel):
    user_id: int = Field(gt=0)


class AssignedUserSummary(BaseModel):
    user_id: int
    full_name: str
    email: str


class ProgramAssignmentData(BaseModel):
    assignment_id: int
    program_id: int
    user: AssignedUserSummary
    assigned_by_user_id: int
    assignment_status: Literal["active", "revoked"]
    assigned_at: datetime
    revoked_at: datetime | None


class ProgramAssignmentListResponse(BaseModel):
    data: list[ProgramAssignmentData]
    message: str


class ProgramAssignmentResponse(BaseModel):
    data: ProgramAssignmentData
    message: str
