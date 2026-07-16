"""PSGC management contracts para sa visual Super Admin workspace."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


PSGCLevel = Literal["region", "province", "city_municipality", "barangay"]
PSGCStatusFilter = Literal["active", "inactive", "all"]

PSGCManagementName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
]
PSGCManagementReason = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=500),
]
PSGCReplacementCode = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=10, max_length=10, pattern=r"^\d{10}$"),
]


class PsgcManagementQuery(BaseModel):
    """Common list/search filters para iisang page lang ang kinukuha."""

    model_config = ConfigDict(populate_by_name=True)

    level: PSGCLevel | None = None
    status: PSGCStatusFilter = "active"
    search: str | None = Field(default=None, min_length=1, max_length=150)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, alias="pageSize", ge=1, le=100)


class PsgcPathSegment(BaseModel):
    level: PSGCLevel
    code: str
    name: str


class PsgcListItem(BaseModel):
    level: PSGCLevel
    code: str
    name: str
    is_active: bool
    parent_label: str | None = None
    city_municipality_type: Literal["city", "municipality"] | None = None


class PsgcPaginationData(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class PsgcListData(BaseModel):
    items: list[PsgcListItem]
    pagination: PsgcPaginationData


class PsgcDependencyData(BaseModel):
    child_count: int
    attendance_address_reference_count: int


class PsgcDetailData(PsgcListItem):
    path: list[PsgcPathSegment]
    dependencies: PsgcDependencyData


class PsgcNameUpdateRequest(BaseModel):
    name: PSGCManagementName
    reason: PSGCManagementReason


class PsgcStatusUpdateRequest(BaseModel):
    is_active: bool
    reason: PSGCManagementReason


class PsgcCodeUpdateRequest(BaseModel):
    new_code: PSGCReplacementCode
    reason: PSGCManagementReason
    confirmed: Literal[True]


class PsgcDeleteRequest(BaseModel):
    reason: PSGCManagementReason
    confirmed: Literal[True]
