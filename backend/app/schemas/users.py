"""Request at response schemas para sa admin user management."""

from typing import Annotated, Literal

from email_validator import EmailNotValidError, validate_email
from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

TrimmedFullName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
]


def normalize_admin_email(email: str) -> str:
    """Normalizes real and local `.test` email addresses for admin accounts."""
    try:
        return validate_email(
            email.strip(),
            check_deliverability=False,
            test_environment=True,
        ).normalized
    except EmailNotValidError as error:
        raise ValueError(str(error)) from error


class CreateUserRequest(BaseModel):
    """Fields na kailangan ng Super Admin sa paggawa ng admin account."""

    full_name: TrimmedFullName
    email: str = Field(max_length=150)
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

    @field_validator("email")
    @classmethod
    def validate_email_address(cls, email: str) -> str:
        return normalize_admin_email(email)


class UpdateUserRequest(BaseModel):
    """Optional profile fields; supplied null is allowed only for org unit."""

    full_name: TrimmedFullName | None = None
    email: str | None = Field(default=None, max_length=150)
    role_id: int | None = Field(default=None, gt=0)
    org_unit_id: int | None = Field(default=None, gt=0)

    @field_validator("full_name", "email", "role_id")
    @classmethod
    def reject_null_required_values(cls, value, info):
        """Kapag sinama ang field, hindi pwedeng null ang required profile value."""
        if value is None:
            raise ValueError(f"{info.field_name} cannot be null.")
        return value

    @field_validator("email")
    @classmethod
    def validate_email_address(cls, email: str | None) -> str | None:
        return normalize_admin_email(email) if email is not None else None

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        """Pinipigilan ang PATCH request na walang kahit anong update."""
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        return self


class UpdateUserStatusRequest(BaseModel):
    """Allowed account states para sa activate/deactivate action."""

    account_status: Literal["active", "inactive"]


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


class UpdateUserStatusResponse(BaseModel):
    data: CreatedUserData
    message: str
