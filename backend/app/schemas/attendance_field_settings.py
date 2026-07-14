"""Schemas para sa fixed attendance-field requirements ng event."""

from pydantic import BaseModel, Field, field_validator


class AttendanceFieldSettingData(BaseModel):
    field_key: str
    field_label: str
    is_required: bool
    is_admin_configurable: bool
    display_order: int


class AttendanceFieldSettingsResponse(BaseModel):
    data: list[AttendanceFieldSettingData]
    message: str


class UpdateAttendanceFieldSettingsRequest(BaseModel):
    requirements: dict[str, bool] = Field(min_length=1, max_length=14)

    @field_validator("requirements")
    @classmethod
    def normalize_field_keys(cls, requirements: dict[str, bool]):
        normalized = {key.strip(): value for key, value in requirements.items()}
        if "" in normalized:
            raise ValueError("Field keys cannot be blank.")
        return normalized
