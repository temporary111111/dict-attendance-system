from types import SimpleNamespace
from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.api.dependencies.auth import require_super_admin
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app
from app.models import AuditLog, PSGCBarangay, PSGCCityMunicipality, PSGCProvince, PSGCRegion


class FakeSession:
    def __init__(self, records=None, *, fail_commit=False):
        self.records = records or {}
        self.fail_commit = fail_commit
        self.added = []
        self.committed = False
        self.rolled_back = False

    def get(self, model, key):
        return self.records.get((model, key))

    def scalars(self, statement):
        model = statement.column_descriptions[0]["entity"]
        records = [
            record
            for (record_model, _), record in self.records.items()
            if record_model is model
        ]
        return SimpleNamespace(all=lambda: records)

    def add(self, record):
        self.added.append(record)
        if not isinstance(record, AuditLog):
            primary_key = next(iter(record.__table__.primary_key.columns)).name
            self.records[(type(record), getattr(record, primary_key))] = record

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("database failed")
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, record):
        return None


def make_client(session, *, authenticated=True):
    app = create_app(
        Settings(jwt_secret_key="test-secret-key-with-more-than-32-bytes")
    )

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    if authenticated:
        app.dependency_overrides[require_super_admin] = lambda: SimpleNamespace(
            user_id=7
        )
    return TestClient(app, raise_server_exceptions=False)


def psgc_workbook_file() -> tuple[str, bytes, str]:
    """Small Excel file para ma-test ang upload endpoint nang walang external file."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["PSGC Code", "Area Name", "Geographic Level"])
    sheet.append(["0300000000", "Region III", "Region"])
    output = BytesIO()
    workbook.save(output)
    return (
        "PSGC-test.xlsx",
        output.getvalue(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def complete_psgc_workbook_file() -> tuple[str, bytes, str]:
    """Complete parent-to-child sample para sa actual import test."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["PSGC Code", "Area Name", "Geographic Level"])
    sheet.append(["0300000000", "Region III", "Region"])
    sheet.append(["0354000000", "Pampanga", "Province"])
    sheet.append(["0354010000", "City of San Fernando", "City"])
    sheet.append(["0354010010", "San Agustin", "Barangay"])
    output = BytesIO()
    workbook.save(output)
    return (
        "PSGC-test.xlsx",
        output.getvalue(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def test_super_admin_can_create_psgc_region_with_audit_log():
    session = FakeSession()
    client = make_client(session)

    response = client.post(
        "/api/admin/psgc/regions",
        json={"region_code": "0300000000", "region_name": "Region III"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "region_code": "0300000000",
        "region_name": "Region III",
    }
    assert session.committed is True
    assert any(isinstance(record, AuditLog) for record in session.added)


def test_saving_existing_region_updates_and_reactivates_it():
    region = PSGCRegion(
        region_code="0300000000",
        region_name="Old name",
        is_active=False,
    )
    session = FakeSession({(PSGCRegion, region.region_code): region})
    client = make_client(session)

    response = client.post(
        "/api/admin/psgc/regions",
        json={"region_code": region.region_code, "region_name": "Region III"},
    )

    assert response.status_code == 200
    assert region.region_name == "Region III"
    assert region.is_active is True


def test_province_rejects_unknown_parent_region():
    client = make_client(FakeSession())

    response = client.post(
        "/api/admin/psgc/provinces",
        json={
            "province_code": "0354000000",
            "province_name": "Pampanga",
            "region_code": "0300000000",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PSGC_PARENT"


def test_psgc_codes_must_be_numeric():
    client = make_client(FakeSession())

    response = client.post(
        "/api/admin/psgc/regions",
        json={"region_code": "REGION-3", "region_name": "Region III"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_psgc_management_requires_authentication():
    client = make_client(FakeSession(), authenticated=False)

    response = client.post(
        "/api/admin/psgc/regions",
        json={"region_code": "0300000000", "region_name": "Region III"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_super_admin_can_preview_psgc_excel_file():
    client = make_client(FakeSession())

    response = client.post(
        "/api/admin/psgc/imports/preview",
        data={"source_version": "PSGC test release"},
        files={"file": psgc_workbook_file()},
    )

    assert response.status_code == 200
    assert response.json()["data"]["valid"] is True
    assert response.json()["data"]["counts"]["regions"] == 1


def test_super_admin_can_import_a_valid_psgc_masterlist_once():
    session = FakeSession()
    client = make_client(session)

    response = client.post(
        "/api/admin/psgc/imports/apply",
        data={"source_version": "PSGC test release"},
        files={"file": complete_psgc_workbook_file()},
    )

    assert response.status_code == 200
    assert response.json()["data"]["created"] == {
        "regions": 1,
        "provinces": 1,
        "cities_municipalities": 1,
        "barangays": 1,
    }
    assert isinstance(session.get(PSGCRegion, "0300000000"), PSGCRegion)
    assert isinstance(session.get(PSGCProvince, "0354000000"), PSGCProvince)
    assert isinstance(session.get(PSGCCityMunicipality, "0354010000"), PSGCCityMunicipality)
    assert isinstance(session.get(PSGCBarangay, "0354010010"), PSGCBarangay)
    assert len([record for record in session.added if isinstance(record, AuditLog)]) == 1
