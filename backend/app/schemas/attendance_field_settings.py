"""Schemas para sa fixed attendance-field requirements ng event."""

from pydantic import BaseModel, Field, field_validator, model_validator


class AttendanceFieldSettingData(BaseModel):
    field_key: str
    field_label: str
    is_required: bool
    is_visible: bool
    is_admin_configurable: bool
    display_order: int


class AttendanceFieldSettingsResponse(BaseModel):
    data: list[AttendanceFieldSettingData]
    message: str


class UpdateAttendanceFieldSettingsRequest(BaseModel):
    requirements: dict[str, bool] | None = Field(default=None, min_length=1, max_length=14)
    visibility: dict[str, bool] | None = Field(default=None, min_length=1, max_length=14)

    @field_validator("requirements", "visibility")
    @classmethod
    def normalize_field_keys(cls, requirements: dict[str, bool] | None):
        if requirements is None:
            return None
        normalized = {key.strip(): value for key, value in requirements.items()}
        if "" in normalized:
            raise ValueError("Field keys cannot be blank.")
        return normalized

    @model_validator(mode="after")
    def require_a_change(self):
        if self.requirements is None and self.visibility is None:
            raise ValueError("Provide requirements or visibility to update.")
        return self
