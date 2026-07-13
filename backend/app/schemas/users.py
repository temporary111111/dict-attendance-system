"""Request at response schemas para sa admin user management."""

from typing import Annotated

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

TrimmedFullName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
]


class CreateUserRequest(BaseModel):
    """Fields na kailangan ng Super Admin sa paggawa ng admin account."""

    full_name: TrimmedFullName
    email: EmailStr = Field(max_length=150)
    password: str = Field(min_length=8, max_length=72)
    role_id: int = Field(gt=0)
    org_unit_id: int | None = Field(default=None, gt=0)

    @field_validator("password")
    @classmethod
    def validate_bcrypt_password_size(cls, password: str) -> str:
        """Nililimitahan ang bytes dahil hanggang 72 bytes ang bcrypt input."""
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes.")
        return password


class UpdateUserRequest(BaseModel):
    """Optional profile fields; supplied null is allowed only for org unit."""

    full_name: TrimmedFullName | None = None
    email: EmailStr | None = Field(default=None, max_length=150)
    role_id: int | None = Field(default=None, gt=0)
    org_unit_id: int | None = Field(default=None, gt=0)

    @field_validator("full_name", "email", "role_id")
    @classmethod
    def reject_null_required_values(cls, value, info):
        """Kapag sinama ang field, hindi pwedeng null ang required profile value."""
        if value is None:
            raise ValueError(f"{info.field_name} cannot be null.")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        """Pinipigilan ang PATCH request na walang kahit anong update."""
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        return self


class UserRoleData(BaseModel):
    role_id: int
    role_name: str


class UserOrganizationalUnitData(BaseModel):
    org_unit_id: int
    unit_name: str


class CreatedUserData(BaseModel):
    user_id: int
    full_name: str
    email: str
    account_status: str
    role: UserRoleData
    org_unit: UserOrganizationalUnitData | None


class CreateUserResponse(BaseModel):
    data: CreatedUserData
    message: str


class UserListResponse(BaseModel):
    data: list[CreatedUserData]
    message: str


class UserDetailResponse(BaseModel):
    data: CreatedUserData
    message: str


class UpdateUserResponse(BaseModel):
    data: CreatedUserData
    message: str
