from sqlalchemy import inspect
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import UniqueConstraint

from app.models import (
    AttendanceRecord,
    AttendanceRecordAddress,
    Base,
)


EXPECTED_TABLES = {
    "roles",
    "organizational_units",
    "users",
    "programs",
    "program_admin_assignments",
    "events",
    "attendance_records",
    "attendance_sheet_exports",
    "audit_logs",
    "psgc_regions",
    "psgc_provinces",
    "psgc_cities_municipalities",
    "psgc_barangays",
    "attendance_record_addresses",
}


def test_model_metadata_contains_all_database_tables():
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_attendance_record_columns_match_fixed_attendance_form():
    table = Base.metadata.tables["attendance_records"]

    assert "affiliation" in table.c
    assert "school_university" not in table.c
    assert "designation_category" in table.c
    assert "consent_documentation_publication" in table.c
    assert "consent_database_processing" in table.c
    assert "signature_text" in table.c
    assert "signature_image_path" in table.c

    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("event_id", "email") in unique_columns


def test_attendance_record_address_references_attendance_and_psgc_tables():
    table = Base.metadata.tables["attendance_record_addresses"]

    foreign_key_targets = {
        foreign_key.parent.name: foreign_key.column.table.name
        for foreign_key in table.foreign_keys
    }

    assert foreign_key_targets == {
        "attendance_id": "attendance_records",
        "region_code": "psgc_regions",
        "province_code": "psgc_provinces",
        "city_municipality_code": "psgc_cities_municipalities",
        "barangay_code": "psgc_barangays",
    }


def test_models_configure_without_relationship_errors():
    configure_mappers()


def test_attendance_record_has_one_address_relationship():
    relationship = inspect(AttendanceRecord).relationships["address"]

    assert relationship.mapper.class_ is AttendanceRecordAddress
    assert relationship.uselist is False
