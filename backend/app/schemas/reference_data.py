"""Response schemas para sa roles at organizational unit dropdown data."""

from pydantic import BaseModel, ConfigDict


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

