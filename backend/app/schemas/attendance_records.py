"""Admin attendance list, detail, at status response contracts."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, StringConstraints

AttendanceStatus = Literal["valid", "duplicate", "invalid", "void"]
TrimmedStatusReason = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=300),
]


class AttendanceRecordSummaryData(BaseModel):
    attendance_id: int
    attendee_name: str
    email: EmailStr
    affiliation: str | None
    designation_category: str | None
    sex: Literal["F", "M"] | None
    attendance_status: AttendanceStatus
    duplicate_flag: bool
    submitted_at: datetime


class PaginationData(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class AttendanceRecordListData(BaseModel):
    items: list[AttendanceRecordSummaryData]
    pagination: PaginationData


class AttendanceRecordListResponse(BaseModel):
    data: AttendanceRecordListData
    message: str


class AttendanceProgramData(BaseModel):
    program_id: int
    program_name: str


class AttendanceEventData(BaseModel):
    event_id: int
    event_title: str
    venue: str
    event_date: date
    event_status: Literal["draft", "open", "closed", "archived"]
    program: AttendanceProgramData


class AddressReferenceData(BaseModel):
    code: str
    name: str


class CityMunicipalityReferenceData(AddressReferenceData):
    type: Literal["city", "municipality"]


class AttendanceAddressData(BaseModel):
    region: AddressReferenceData
    province: AddressReferenceData | None
    city_municipality: CityMunicipalityReferenceData
    barangay: AddressReferenceData
    street_address: str | None
    postal_code: str | None


class AttendanceSignatureData(BaseModel):
    typed_name: str | None
    has_image: bool
    image_url: str | None


class AttendanceRecordDetailData(BaseModel):
    attendance_id: int
    first_name: str
    middle_name: str | None
    last_name: str
    suffix: str | None
    email: EmailStr
    affiliation: str | None
    designation_category: str | None
    sex: Literal["F", "M"] | None
    consent_documentation_publication: bool
    consent_database_processing: bool
    attendance_status: AttendanceStatus
    duplicate_flag: bool
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime
    event: AttendanceEventData
    address: AttendanceAddressData | None
    signature: AttendanceSignatureData


class AttendanceRecordDetailResponse(BaseModel):
    data: AttendanceRecordDetailData
    message: str


class UpdateAttendanceStatusRequest(BaseModel):
    attendance_status: AttendanceStatus
    reason: TrimmedStatusReason
