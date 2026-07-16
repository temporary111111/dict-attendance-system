from io import BytesIO
from types import SimpleNamespace

import pytest
from openpyxl import Workbook

from app.models import AuditLog, PSGCBarangay, PSGCCityMunicipality, PSGCProvince, PSGCRegion
from app.services.psgc_import_service import (
    PSGCImportValidationError,
    import_psgc_workbook,
    preview_psgc_workbook,
)


def build_workbook(rows: list[tuple[str, str, str]]) -> bytes:
    """Gumagawa ng maliit na PSGC Excel file para sa importer tests."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "PSGC Data"
    sheet.append(["PSGC Code", "Area Name", "Geographic Level"])
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


class ImportSession:
    """Maliit na in-memory session para ma-check ang parent code ng imported rows."""

    def __init__(self):
        self.records = {}

    def add(self, record):
        if isinstance(record, AuditLog):
            return
        primary_key = next(iter(record.__table__.primary_key.columns)).name
        self.records[(type(record), getattr(record, primary_key))] = record

    def scalars(self, statement):
        model = statement.column_descriptions[0]["entity"]
        records = [
            record
            for (record_model, _), record in self.records.items()
            if record_model is model
        ]
        return SimpleNamespace(all=lambda: records)

    def commit(self):
        return None

    def rollback(self):
        return None


def test_preview_reads_a_complete_psgc_hierarchy():
    workbook = build_workbook(
        [
            ("0300000000", "Region III", "Region"),
            ("0354000000", "Pampanga", "Province"),
            ("0354010000", "City of San Fernando", "City"),
            ("0354010010", "San Agustin", "Barangay"),
        ]
    )

    preview = preview_psgc_workbook(workbook, "PSGC-test.xlsx")

    assert preview["valid"] is True
    assert preview["sheet_name"] == "PSGC Data"
    assert preview["counts"] == {
        "regions": 1,
        "provinces": 1,
        "cities_municipalities": 1,
        "barangays": 1,
    }
    assert preview["errors"] == []


def test_preview_rejects_barangay_without_its_city_parent():
    workbook = build_workbook(
        [
            ("0300000000", "Region III", "Region"),
            ("0354000000", "Pampanga", "Province"),
            ("0354010010", "San Agustin", "Barangay"),
        ]
    )

    with pytest.raises(PSGCImportValidationError) as error:
        preview_psgc_workbook(workbook, "PSGC-test.xlsx")

    assert "missing city or municipality" in error.value.errors[0].lower()


def test_preview_allows_city_without_a_province_parent():
    workbook = build_workbook(
        [
            ("1300000000", "National Capital Region", "Region"),
            ("1374040000", "City of Manila", "City"),
        ]
    )

    preview = preview_psgc_workbook(workbook, "PSGC-test.xlsx")

    assert preview["valid"] is True
    assert preview["counts"]["cities_municipalities"] == 1


def test_preview_maps_submunicipality_barangays_to_the_parent_city():
    workbook = build_workbook(
        [
            ("1300000000", "National Capital Region", "Region"),
            ("1380600000", "City of Manila", "City"),
            ("1380610000", "Malate", "SubMun"),
            ("1380610004", "Barangay 689", "Bgy"),
        ]
    )

    preview = preview_psgc_workbook(workbook, "PSGC-test.xlsx")

    assert preview["valid"] is True
    assert preview["counts"]["cities_municipalities"] == 1
    assert preview["counts"]["barangays"] == 1


def test_import_saves_submunicipality_barangay_under_the_parent_city():
    workbook = build_workbook(
        [
            ("1300000000", "National Capital Region", "Region"),
            ("1380600000", "City of Manila", "City"),
            ("1380610000", "Malate", "SubMun"),
            ("1380610004", "Barangay 689", "Bgy"),
        ]
    )
    session = ImportSession()

    import_psgc_workbook(
        session,
        workbook,
        "PSGC-test.xlsx",
        "PSGC test release",
        user_id=7,
    )

    barangay = session.records[(PSGCBarangay, "1380610004")]
    assert barangay.city_municipality_code == "1380600000"


def test_import_uses_the_revision_one_three_digit_province_segment():
    workbook = build_workbook(
        [
            ("0500000000", "Region V", "Region"),
            ("0500500000", "Albay", "Province"),
            ("0500506000", "City of Legazpi", "City"),
            ("0500506001", "Barangay 1", "Bgy"),
        ]
    )
    session = ImportSession()

    import_psgc_workbook(
        session,
        workbook,
        "PSGC-test.xlsx",
        "PSGC test release",
        user_id=7,
    )

    city = session.records[(PSGCCityMunicipality, "0500506000")]
    assert city.province_code == "0500500000"


def test_preview_maps_special_group_barangays_to_the_child_city():
    workbook = build_workbook(
        [
            ("0900000000", "Region IX", "Region"),
            ("0990100000", "City of Isabela (Not a Province)", ""),
            ("0990101000", "City of Isabela", "City"),
            ("0990101002", "Aguada", "Bgy"),
        ]
    )

    preview = preview_psgc_workbook(workbook, "PSGC-test.xlsx")

    assert preview["valid"] is True
    assert preview["counts"]["cities_municipalities"] == 1
    assert preview["counts"]["barangays"] == 1


def test_preview_rejects_workbook_without_psgc_headers():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Code", "Place"])
    output = BytesIO()
    workbook.save(output)

    with pytest.raises(PSGCImportValidationError) as error:
        preview_psgc_workbook(output.getvalue(), "PSGC-test.xlsx")

    assert "headers" in error.value.errors[0].lower()
