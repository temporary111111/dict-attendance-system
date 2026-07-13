"""Schemas para sa roles at organizational unit management."""

from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

TrimmedUnitName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]
TrimmedUnitLabel = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
]


class RoleItem(BaseModel):
    """Public fields ng role na kailangan sa admin user management."""

    model_config = ConfigDict(from_attributes=True)

    role_id: int
    role_name: str
    description: str | None


class RoleListResponse(BaseModel):
    data: list[RoleItem]
    message: str


class OrganizationalUnitItem(BaseModel):
    """Unit fields kasama ang parent ID para mabuo ang DICT hierarchy."""

    model_config = ConfigDict(from_attributes=True)

    org_unit_id: int
    parent_unit_id: int | None
    unit_name: str
    unit_type: str
    unit_code: str | None


class OrganizationalUnitListResponse(BaseModel):
    data: list[OrganizationalUnitItem]
    message: str


class CreateOrganizationalUnitRequest(BaseModel):
    """Fields para sa root o child DICT organizational unit."""

    unit_name: TrimmedUnitName
    unit_type: TrimmedUnitLabel
    unit_code: TrimmedUnitLabel | None = None
    parent_unit_id: int | None = Field(default=None, gt=0)

    @field_validator("unit_type")
    @classmethod
    def normalize_unit_type(cls, unit_type: str) -> str:
        return unit_type.lower()

    @field_validator("unit_code")
    @classmethod
    def normalize_unit_code(cls, unit_code: str | None) -> str | None:
        return unit_code.upper() if unit_code is not None else None


class CreateOrganizationalUnitResponse(BaseModel):
    data: OrganizationalUnitItem
    message: str
