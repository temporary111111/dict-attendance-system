from datetime import datetime
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app


class FakeSession:
    def __init__(
        self,
        *,
        event=None,
        duplicate_attendance_id=None,
        psgc_records=None,
        fail_commit=False,
        commit_error_code=1062,
    ):
        self.event = event
        self.duplicate_attendance_id = duplicate_attendance_id
        self.psgc_records = psgc_records or {}
        self.fail_commit = fail_commit
        self.commit_error_code = commit_error_code
        self.added_attendance = None
        self.committed = False

    def scalar(self, statement):
        statement_text = str(statement)
        if "attendance_records.attendance_id" in statement_text:
            return self.duplicate_attendance_id
        return self.event

    def get(self, model, key):
        return self.psgc_records.get((model.__name__, key))

    def add(self, attendance):
        self.added_attendance = attendance

    def commit(self):
        if self.fail_commit:
            raise IntegrityError(
                "INSERT",
                {},
                Exception(self.commit_error_code, "database constraint error"),
            )
        self.committed = True

    def rollback(self):
        self.committed = False

    def refresh(self, attendance):
        if attendance.attendance_id is None:
            attendance.attendance_id = 20
        if attendance.submitted_at is None:
            attendance.submitted_at = datetime(2026, 8, 15, 9, 30, 0)


def make_settings(signature_directory=None) -> Settings:
    data = {"jwt_secret_key": "test-secret-key-with-more-than-32-bytes"}
    if signature_directory is not None:
        data["signature_directory"] = signature_directory
    return Settings(**data)


def make_client(session, *, signature_directory=None) -> TestClient:
    app = create_app(make_settings(signature_directory))

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def make_event(status="open"):
    return SimpleNamespace(
        event_id=5,
        event_code="public-code",
        event_status=status,
    )


def make_psgc_records():
    region = SimpleNamespace(
        region_code="0300000000",
        is_active=True,
    )
    province = SimpleNamespace(
        province_code="0354000000",
        region_code="0300000000",
        is_active=True,
    )
    city = SimpleNamespace(
        city_municipality_code="0354160000",
        region_code="0300000000",
        province_code="0354000000",
        is_active=True,
    )
    barangay = SimpleNamespace(
        barangay_code="0354160010",
        city_municipality_code="0354160000",
        is_active=True,
    )
    return {
        ("PSGCRegion", region.region_code): region,
        ("PSGCProvince", province.province_code): province,
        ("PSGCCityMunicipality", city.city_municipality_code): city,
        ("PSGCBarangay", barangay.barangay_code): barangay,
    }


def valid_form_data(*, include_address=True) -> dict:
    data = {
        "first_name": "  Maria  ",
        "middle_name": "Santos",
        "last_name": "  Reyes  ",
        "suffix": "",
        "affiliation": "  Municipality of San Fernando  ",
        "designation_category": "  Government Official  ",
        "sex": "F",
        "email": "MARIA.REYES@EXAMPLE.COM",
        "consent_documentation_publication": "false",
        "consent_database_processing": "true",
        "signature_text": "  Maria Santos Reyes  ",
    }
    if include_address:
        data.update(
            {
                "region_code": "0300000000",
                "province_code": "0354000000",
                "city_municipality_code": "0354160000",
                "barangay_code": "0354160010",
                "street_address": "  MacArthur Highway  ",
                "postal_code": "2000",
            }
        )
    return data


def make_jpeg_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (80, 30), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


def test_submit_attendance_saves_normalized_record_and_psgc_address():
    session = FakeSession(
        event=make_event(),
        psgc_records=make_psgc_records(),
    )
    client = make_client(session)

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=valid_form_data(),
    )

    assert response.status_code == 201
    assert response.json() == {
        "data": {
            "attendance_id": 20,
            "event_code": "public-code",
            "attendee_name": "Maria Santos Reyes",
            "attendance_status": "valid",
            "submitted_at": "2026-08-15T09:30:00",
        },
        "message": "Attendance submitted successfully.",
    }
    attendance = session.added_attendance
    assert attendance.email == "maria.reyes@example.com"
    assert attendance.consent_documentation_publication is False
    assert attendance.duplicate_flag is False
    assert attendance.address.region_code == "0300000000"
    assert attendance.address.street_address == "MacArthur Highway"
    assert session.committed is True


def test_submit_attendance_treats_empty_signature_image_as_not_uploaded():
    session = FakeSession(event=make_event())
    client = make_client(session)
    data = valid_form_data(include_address=False)
    data["signature_image"] = ""

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=data,
    )

    assert response.status_code == 201
    assert session.added_attendance.signature_image_path is None


def test_submit_attendance_rejects_duplicate_email_for_event():
    session = FakeSession(
        event=make_event(),
        duplicate_attendance_id=9,
    )
    client = make_client(session)

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=valid_form_data(include_address=False),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_ATTENDANCE"
    assert session.added_attendance is None


def test_submit_attendance_rejects_closed_event():
    client = make_client(FakeSession(event=make_event("closed")))

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=valid_form_data(include_address=False),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVENT_NOT_OPEN"


def test_submit_attendance_requires_database_processing_consent():
    data = valid_form_data(include_address=False)
    data["consent_database_processing"] = "false"
    client = make_client(FakeSession(event=make_event()))

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=data,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_submit_attendance_rejects_incomplete_address():
    data = valid_form_data(include_address=False)
    data["region_code"] = "0300000000"
    client = make_client(FakeSession(event=make_event()))

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=data,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_submit_attendance_rejects_mismatched_psgc_hierarchy():
    records = make_psgc_records()
    records[("PSGCBarangay", "0354160010")].city_municipality_code = "other-city"
    session = FakeSession(event=make_event(), psgc_records=records)
    client = make_client(session)

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=valid_form_data(),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PSGC_ADDRESS"


def test_submit_attendance_requires_typed_or_image_signature():
    data = valid_form_data(include_address=False)
    data["signature_text"] = ""
    client = make_client(FakeSession(event=make_event()))

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=data,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SIGNATURE_REQUIRED"


def test_submit_attendance_stores_uploaded_signature_privately(tmp_path):
    session = FakeSession(event=make_event())
    client = make_client(session, signature_directory=tmp_path)
    data = valid_form_data(include_address=False)
    data["signature_text"] = ""

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=data,
        files={
            "signature_image": (
                "signature.jpg",
                make_jpeg_bytes(),
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 201
    stored_path = session.added_attendance.signature_image_path
    assert stored_path.endswith(".png")
    assert (tmp_path / stored_path).read_bytes().startswith(b"\x89PNG")
    assert client.get(f"/media/signatures/{stored_path}").status_code == 404


def test_submit_attendance_rejects_invalid_signature_image(tmp_path):
    session = FakeSession(event=make_event())
    client = make_client(session, signature_directory=tmp_path)
    data = valid_form_data(include_address=False)
    data["signature_text"] = ""

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=data,
        files={"signature_image": ("fake.png", b"not-an-image", "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_SIGNATURE_IMAGE"


def test_duplicate_race_removes_new_signature_file(tmp_path):
    session = FakeSession(event=make_event(), fail_commit=True)
    client = make_client(session, signature_directory=tmp_path)
    data = valid_form_data(include_address=False)
    data["signature_text"] = ""

    response = client.post(
        "/api/public/events/public-code/attendance",
        data=data,
        files={
            "signature_image": (
                "signature.jpg",
                make_jpeg_bytes(),
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_ATTENDANCE"
    assert list(tmp_path.rglob("*.png")) == []


def test_non_duplicate_integrity_error_is_not_hidden_and_removes_signature(
    tmp_path,
):
    session = FakeSession(
        event=make_event(),
        fail_commit=True,
        commit_error_code=1452,
    )
    client = make_client(session, signature_directory=tmp_path)
    data = valid_form_data(include_address=False)
    data["signature_text"] = ""

    with pytest.raises(IntegrityError):
        client.post(
            "/api/public/events/public-code/attendance",
            data=data,
            files={
                "signature_image": (
                    "signature.jpg",
                    make_jpeg_bytes(),
                    "image/jpeg",
                )
            },
        )

    assert list(tmp_path.rglob("*.png")) == []


def test_submission_openapi_uses_flat_multipart_form():
    client = make_client(FakeSession(event=make_event()))

    schema = client.app.openapi()
    operation = schema["paths"][
        "/api/public/events/{event_code}/attendance"
    ]["post"]
    body_schema = operation["requestBody"]["content"]["multipart/form-data"][
        "schema"
    ]
    component_name = body_schema["$ref"].rsplit("/", 1)[-1]
    properties = schema["components"]["schemas"][component_name]["properties"]

    assert "first_name" in properties
    assert "signature_image" in properties
    assert "payload" not in properties
