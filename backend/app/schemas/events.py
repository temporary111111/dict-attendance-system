"""Request at response schemas para sa event management."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    StringConstraints,
    field_validator,
    model_validator,
)

TrimmedEventTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]
TrimmedEventDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=5000),
]
TrimmedVenue = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]


class EventProgramSummary(BaseModel):
    program_id: int
    program_name: str


class EventData(BaseModel):
    event_id: int
    program: EventProgramSummary
    created_by_user_id: int
    event_title: str
    event_description: str | None
    venue: str
    event_date: date
    event_code: str
    public_attendance_url: str | None
    qr_code_path: str | None
    event_status: Literal["draft", "open", "closed", "archived"]
    opened_at: datetime | None
    closed_at: datetime | None


class EventListResponse(BaseModel):
    data: list[EventData]
    message: str


class EventResponse(BaseModel):
    data: EventData
    message: str


class CreateEventRequest(BaseModel):
    event_title: TrimmedEventTitle
    event_description: TrimmedEventDescription | None = None
    venue: TrimmedVenue
    event_date: date


class UpdateEventRequest(BaseModel):
    event_title: TrimmedEventTitle | None = None
    event_description: TrimmedEventDescription | None = None
    venue: TrimmedVenue | None = None
    event_date: date | None = None

    @field_validator("event_title", "venue", "event_date")
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
