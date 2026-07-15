"""Validated Super Admin inputs para sa PSGC reference records."""

from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints


PSGCCode = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=10, pattern=r"^\d+$"),
]
PSGCName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
]


class UpsertPSGCRegionRequest(BaseModel):
    region_code: PSGCCode
    region_name: PSGCName


class UpsertPSGCProvinceRequest(BaseModel):
    province_code: PSGCCode
    region_code: PSGCCode
    province_name: PSGCName


class UpsertPSGCCityMunicipalityRequest(BaseModel):
    city_municipality_code: PSGCCode
    region_code: PSGCCode
    province_code: PSGCCode | None = None
    city_municipality_name: PSGCName
    city_municipality_type: Literal["city", "municipality"]


class UpsertPSGCBarangayRequest(BaseModel):
    barangay_code: PSGCCode
    city_municipality_code: PSGCCode
    barangay_name: PSGCName
