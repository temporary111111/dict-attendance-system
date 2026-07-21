"""Public event, PSGC, at attendance submission response contracts."""

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import UploadFile
from pydantic import (
    BaseModel,
    EmailStr,
    StringConstraints,
    field_validator,
    model_validator,
)

TrimmedFirstOrLastName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]
TrimmedMiddleName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]
TrimmedSuffix = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=30),
]
TrimmedAffiliation = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]
TrimmedDesignation = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
]
TrimmedPSGCCode = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=10),
]
TrimmedStreetAddress = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
TrimmedPostalCode = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=10),
]


class PublicEventProgramData(BaseModel):
    program_id: int
    program_name: str
    logo_url: str | None = None


class PublicEventData(BaseModel):
    event_code: str
    event_title: str
    event_description: str | None
    venue: str
    event_date: date
    event_status: Literal["draft", "open", "closed"]
    accepting_attendance: bool
    attendance_field_requirements: dict[str, bool]
    attendance_field_visibility: dict[str, bool]
    program: PublicEventProgramData


class PublicEventResponse(BaseModel):
    data: PublicEventData
    message: str


class PSGCRegionData(BaseModel):
    region_code: str
    region_name: str


class PSGCRegionListResponse(BaseModel):
    data: list[PSGCRegionData]
    message: str


class PSGCProvinceData(BaseModel):
    province_code: str
    region_code: str
    province_name: str


class PSGCProvinceListResponse(BaseModel):
    data: list[PSGCProvinceData]
    message: str


class PSGCCityMunicipalityData(BaseModel):
    city_municipality_code: str
    region_code: str
    province_code: str | None
    city_municipality_name: str
    city_municipality_type: Literal["city", "municipality"]


class PSGCCityMunicipalityListResponse(BaseModel):
    data: list[PSGCCityMunicipalityData]
    message: str


class PSGCBarangayData(BaseModel):
    barangay_code: str
    city_municipality_code: str
    barangay_name: str


class PSGCBarangayListResponse(BaseModel):
    data: list[PSGCBarangayData]
    message: str


class AttendanceSubmissionRequest(BaseModel):
    """Fixed attendee fields na galing sa multipart public form."""

    first_name: TrimmedFirstOrLastName
    middle_name: TrimmedMiddleName | None = None
    last_name: TrimmedFirstOrLastName
    suffix: TrimmedSuffix | None = None
    affiliation: TrimmedAffiliation | None = None
    designation_category: TrimmedDesignation | None = None
    sex: Literal["F", "M"] | None = None
    email: EmailStr
    consent_documentation_publication: bool | None = None
    consent_database_processing: bool
    signature_image: UploadFile | None = None
    region_code: TrimmedPSGCCode | None = None
    province_code: TrimmedPSGCCode | None = None
    city_municipality_code: TrimmedPSGCCode | None = None
    barangay_code: TrimmedPSGCCode | None = None
    street_address: TrimmedStreetAddress | None = None
    postal_code: TrimmedPostalCode | None = None

    @field_validator(
        "middle_name",
        "suffix",
        "affiliation",
        "designation_category",
        "sex",
        "consent_documentation_publication",
        "signature_image",
        "region_code",
        "province_code",
        "city_municipality_code",
        "barangay_code",
        "street_address",
        "postal_code",
        mode="before",
    )
    @classmethod
    def convert_blank_optional_values(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, email: EmailStr) -> str:
        return str(email).strip().lower()

    @model_validator(mode="after")
    def validate_consent_and_address(self):
        if not self.consent_database_processing:
            raise ValueError("Database processing consent is required.")

        address_values = (
            self.region_code,
            self.province_code,
            self.city_municipality_code,
            self.barangay_code,
            self.street_address,
            self.postal_code,
        )
        if any(value is not None for value in address_values):
            if not all(
                (
                    self.region_code,
                    self.city_municipality_code,
                    self.barangay_code,
                )
            ):
                raise ValueError(
                    "Region, city or municipality, and barangay are required."
                )
        return self

    @property
    def has_address(self) -> bool:
        return self.region_code is not None


class AttendanceSubmissionData(BaseModel):
    attendance_id: int
    event_code: str
    attendee_name: str
    attendance_status: Literal["valid"]
    submitted_at: datetime


class AttendanceSubmissionResponse(BaseModel):
    data: AttendanceSubmissionData
    message: str
