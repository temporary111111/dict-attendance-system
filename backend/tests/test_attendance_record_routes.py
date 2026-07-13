from datetime import date, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.dependencies.auth import get_current_user
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app


class FakeSession:
    def __init__(
        self,
        *,
        event=None,
        listed_records=None,
        total_items=0,
        assignment_id=None,
        attendance_record=None,
        fail_commit=False,
    ):
        self.event = event
        self.listed_records = listed_records or []
        self.total_items = total_items
        self.assignment_id = assignment_id
        self.attendance_record = attendance_record
        self.fail_commit = fail_commit
        self.checked_statements = []
        self.added_objects = []
        self.committed = False
        self.rolled_back = False

    def get(self, model, key):
        if model.__name__ == "Event" and self.event is not None:
            if self.event.event_id == key:
                return self.event
        return None

    def scalar(self, statement):
        statement_text = str(statement)
        self.checked_statements.append(statement_text)
        if "program_admin_assignments.assignment_id" in statement_text:
            return self.assignment_id
        if "count(attendance_records.attendance_id)" in statement_text:
            return self.total_items
        if "FROM attendance_records" in statement_text:
            return self.attendance_record
        return None

    def scalars(self, statement):
        self.checked_statements.append(str(statement))
        return SimpleNamespace(all=lambda: self.listed_records)

    def add(self, record):
        self.added_objects.append(record)

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("database write failed")
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, record):
        return None


def make_settings(signature_directory=None) -> Settings:
    data = {"jwt_secret_key": "test-secret-key-with-more-than-32-bytes"}
    if signature_directory is not None:
        data["signature_directory"] = signature_directory
    return Settings(**data)


def make_user(role_name="super_admin", user_id=1):
    return SimpleNamespace(
        user_id=user_id,
        role=SimpleNamespace(role_name=role_name, is_active=True),
        account_status="active",
    )


def make_program(program_id=3):
    return SimpleNamespace(
        program_id=program_id,
        program_name="Free Wi-Fi for All",
    )


def make_event(event_id=5, program_id=3, event_status="closed"):
    program = make_program(program_id)
    return SimpleNamespace(
        event_id=event_id,
        program_id=program_id,
        program=program,
        event_title="Digital Inclusion Orientation",
        venue="DICT Regional Office",
        event_date=date(2026, 8, 15),
        event_status=event_status,
    )


def make_address():
    return SimpleNamespace(
        region_code="0300000000",
        province_code="0354000000",
        city_municipality_code="0354160000",
        barangay_code="0354160010",
        street_address="MacArthur Highway",
        postal_code="2000",
        region=SimpleNamespace(
            region_code="0300000000",
            region_name="Region III (Central Luzon)",
            is_active=False,
        ),
        province=SimpleNamespace(
            province_code="0354000000",
            province_name="Pampanga",
            is_active=False,
        ),
        city_municipality=SimpleNamespace(
            city_municipality_code="0354160000",
            city_municipality_name="City of San Fernando",
            city_municipality_type="city",
            is_active=False,
        ),
        barangay=SimpleNamespace(
            barangay_code="0354160010",
            barangay_name="San Agustin",
            is_active=False,
        ),
    )


def make_attendance(
    attendance_id=20,
    attendance_status="valid",
    *,
    event=None,
    address=None,
    signature_text="Maria Santos Reyes",
    signature_image_path=None,
):
    return SimpleNamespace(
        attendance_id=attendance_id,
        event_id=5,
        event=event or make_event(),
        first_name="Maria",
        middle_name="Santos",
        last_name="Reyes",
        suffix=None,
        email="maria.reyes@example.com",
        affiliation="Municipality of San Fernando",
        designation_category="Government Official",
        sex="F",
        consent_documentation_publication=False,
        consent_database_processing=True,
        signature_text=signature_text,
        signature_image_path=signature_image_path,
        attendance_status=attendance_status,
        duplicate_flag=False,
        submitted_at=datetime(2026, 8, 15, 9, 30),
        created_at=datetime(2026, 8, 15, 9, 30),
        updated_at=datetime(2026, 8, 15, 9, 30),
        address=address,
    )


def make_client(
    session,
    *,
    current_user=None,
    signature_directory=None,
) -> TestClient:
    app = create_app(make_settings(signature_directory))

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return TestClient(app)


def test_list_event_attendance_returns_paginated_summary_for_super_admin():
    session = FakeSession(
        event=make_event(),
        listed_records=[make_attendance()],
        total_items=1,
    )
    client = make_client(session, current_user=make_user())

    response = client.get("/api/events/5/attendance-records")

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "items": [
                {
                    "attendance_id": 20,
                    "attendee_name": "Maria Santos Reyes",
                    "email": "maria.reyes@example.com",
                    "affiliation": "Municipality of San Fernando",
                    "designation_category": "Government Official",
                    "sex": "F",
                    "attendance_status": "valid",
                    "duplicate_flag": False,
                    "submitted_at": "2026-08-15T09:30:00",
                }
            ],
            "pagination": {
                "page": 1,
                "page_size": 25,
                "total_items": 1,
                "total_pages": 1,
            },
        },
        "message": "Attendance records retrieved.",
    }


def test_assigned_program_admin_can_list_event_attendance():
    session = FakeSession(
        event=make_event(),
        listed_records=[make_attendance()],
        total_items=1,
        assignment_id=9,
    )
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.get("/api/events/5/attendance-records")

    assert response.status_code == 200
    assert any(
        "program_admin_assignments.assignment_id" in statement
        for statement in session.checked_statements
    )
    assert any(
        "assignment_status" in statement
        for statement in session.checked_statements
    )


def test_unassigned_program_admin_cannot_list_event_attendance():
    session = FakeSession(event=make_event())
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.get("/api/events/5/attendance-records")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_list_event_attendance_returns_event_not_found():
    client = make_client(FakeSession(), current_user=make_user())

    response = client.get("/api/events/999/attendance-records")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVENT_NOT_FOUND"


def test_list_event_attendance_applies_status_search_and_pagination():
    session = FakeSession(
        event=make_event(),
        listed_records=[make_attendance(attendance_status="void")],
        total_items=26,
    )
    client = make_client(session, current_user=make_user())

    response = client.get(
        "/api/events/5/attendance-records",
        params={
            "page": 2,
            "pageSize": 25,
            "status": "void",
            "search": "maria reyes",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["pagination"] == {
        "page": 2,
        "page_size": 25,
        "total_items": 26,
        "total_pages": 2,
    }
    statements = "\n".join(session.checked_statements)
    assert "attendance_status" in statements
    assert "lower" in statements.lower()
    assert "LIMIT" in statements
    assert "OFFSET" in statements
    assert "submitted_at DESC" in statements
    assert "attendance_id DESC" in statements


@pytest.mark.parametrize(
    "query_string",
    [
        "page=0",
        "pageSize=0",
        "pageSize=101",
        "status=unknown",
        f"search={'x' * 101}",
    ],
)
def test_list_event_attendance_validates_query_parameters(query_string):
    client = make_client(
        FakeSession(event=make_event()),
        current_user=make_user(),
    )

    response = client.get(f"/api/events/5/attendance-records?{query_string}")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_event_attendance_requires_authentication():
    client = make_client(FakeSession(event=make_event()))

    response = client.get("/api/events/5/attendance-records")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_attendance_detail_returns_event_program_consent_and_historical_address():
    attendance = make_attendance(address=make_address())
    session = FakeSession(attendance_record=attendance)
    client = make_client(session, current_user=make_user())

    response = client.get("/api/attendance-records/20")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "attendance_id": 20,
        "first_name": "Maria",
        "middle_name": "Santos",
        "last_name": "Reyes",
        "suffix": None,
        "email": "maria.reyes@example.com",
        "affiliation": "Municipality of San Fernando",
        "designation_category": "Government Official",
        "sex": "F",
        "consent_documentation_publication": False,
        "consent_database_processing": True,
        "attendance_status": "valid",
        "duplicate_flag": False,
        "submitted_at": "2026-08-15T09:30:00",
        "created_at": "2026-08-15T09:30:00",
        "updated_at": "2026-08-15T09:30:00",
        "event": {
            "event_id": 5,
            "event_title": "Digital Inclusion Orientation",
            "venue": "DICT Regional Office",
            "event_date": "2026-08-15",
            "event_status": "closed",
            "program": {
                "program_id": 3,
                "program_name": "Free Wi-Fi for All",
            },
        },
        "address": {
            "region": {
                "code": "0300000000",
                "name": "Region III (Central Luzon)",
            },
            "province": {
                "code": "0354000000",
                "name": "Pampanga",
            },
            "city_municipality": {
                "code": "0354160000",
                "name": "City of San Fernando",
                "type": "city",
            },
            "barangay": {
                "code": "0354160010",
                "name": "San Agustin",
            },
            "street_address": "MacArthur Highway",
            "postal_code": "2000",
        },
        "signature": {
            "typed_name": "Maria Santos Reyes",
            "has_image": False,
            "image_url": None,
        },
    }
    assert "signature_image_path" not in response.text


def test_attendance_detail_allows_assigned_program_admin():
    session = FakeSession(
        attendance_record=make_attendance(),
        assignment_id=9,
    )
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.get("/api/attendance-records/20")

    assert response.status_code == 200


def test_attendance_detail_rejects_unassigned_program_admin():
    session = FakeSession(attendance_record=make_attendance())
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.get("/api/attendance-records/20")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_attendance_detail_returns_record_not_found():
    client = make_client(FakeSession(), current_user=make_user())

    response = client.get("/api/attendance-records/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ATTENDANCE_RECORD_NOT_FOUND"


def test_protected_signature_returns_private_png(tmp_path):
    relative_path = "event-5/signature-test.png"
    signature_path = tmp_path / relative_path
    signature_path.parent.mkdir(parents=True)
    Image.new("RGBA", (20, 10), "white").save(signature_path, format="PNG")
    attendance = make_attendance(signature_image_path=relative_path)
    client = make_client(
        FakeSession(attendance_record=attendance),
        current_user=make_user(),
        signature_directory=tmp_path,
    )

    response = client.get("/api/attendance-records/20/signature")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "private, no-store"
    assert response.content.startswith(b"\x89PNG")


@pytest.mark.parametrize(
    ("relative_path", "create_outside_file"),
    [
        (None, False),
        ("event-5/missing.png", False),
        ("../outside.png", True),
    ],
)
def test_protected_signature_rejects_unavailable_or_unsafe_file(
    tmp_path,
    relative_path,
    create_outside_file,
):
    if create_outside_file:
        (tmp_path.parent / "outside.png").write_bytes(b"outside")
    attendance = make_attendance(
        signature_text="Maria Santos Reyes" if relative_path is None else None,
        signature_image_path=relative_path,
    )
    client = make_client(
        FakeSession(attendance_record=attendance),
        current_user=make_user(),
        signature_directory=tmp_path,
    )

    response = client.get("/api/attendance-records/20/signature")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SIGNATURE_IMAGE_NOT_FOUND"


def test_protected_signature_requires_authentication(tmp_path):
    client = make_client(
        FakeSession(attendance_record=make_attendance()),
        signature_directory=tmp_path,
    )

    response = client.get("/api/attendance-records/20/signature")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_assigned_program_admin_updates_status_and_creates_audit():
    attendance = make_attendance()
    session = FakeSession(
        attendance_record=attendance,
        assignment_id=9,
    )
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.patch(
        "/api/attendance-records/20/status",
        json={
            "attendance_status": "void",
            "reason": "Submitted using the wrong attendee email.",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["attendance_status"] == "void"
    assert attendance.attendance_status == "void"
    assert session.committed is True
    assert len(session.added_objects) == 1
    audit = session.added_objects[0]
    assert audit.user_id == 2
    assert audit.action == "attendance_status_changed"
    assert audit.entity_type == "attendance_record"
    assert audit.entity_id == 20
    assert audit.old_values_json == {"attendance_status": "valid"}
    assert audit.new_values_json == {
        "attendance_status": "void",
        "reason": "Submitted using the wrong attendee email.",
    }
    assert "valid to void" in audit.description
    assert audit.ip_address == "testclient"
    assert audit.user_agent == "testclient"


@pytest.mark.parametrize("new_status", ["valid", "duplicate", "invalid", "void"])
def test_super_admin_can_set_every_attendance_status(new_status):
    attendance = make_attendance(attendance_status="duplicate")
    session = FakeSession(attendance_record=attendance)
    client = make_client(session, current_user=make_user())

    response = client.patch(
        "/api/attendance-records/20/status",
        json={
            "attendance_status": new_status,
            "reason": "Reviewed by the Super Admin.",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["attendance_status"] == new_status


def test_unassigned_program_admin_cannot_update_attendance_status():
    attendance = make_attendance()
    session = FakeSession(attendance_record=attendance)
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.patch(
        "/api/attendance-records/20/status",
        json={"attendance_status": "void", "reason": "Invalid submission."},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert attendance.attendance_status == "valid"
    assert session.added_objects == []


def test_same_attendance_status_is_idempotent_without_audit_or_commit():
    attendance = make_attendance()
    session = FakeSession(attendance_record=attendance)
    client = make_client(session, current_user=make_user())

    response = client.patch(
        "/api/attendance-records/20/status",
        json={"attendance_status": "valid", "reason": "Confirmed as valid."},
    )

    assert response.status_code == 200
    assert session.added_objects == []
    assert session.committed is False


@pytest.mark.parametrize(
    "payload",
    [
        {"attendance_status": "void"},
        {"attendance_status": "void", "reason": " x "},
        {"attendance_status": "unknown", "reason": "Reviewed record."},
        {"attendance_status": "void", "reason": "x" * 301},
    ],
)
def test_update_attendance_status_validates_payload(payload):
    client = make_client(
        FakeSession(attendance_record=make_attendance()),
        current_user=make_user(),
    )

    response = client.patch("/api/attendance-records/20/status", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_status_and_audit_transaction_rolls_back_together():
    attendance = make_attendance()
    session = FakeSession(
        attendance_record=attendance,
        fail_commit=True,
    )
    client = make_client(session, current_user=make_user())

    with pytest.raises(RuntimeError, match="database write failed"):
        client.patch(
            "/api/attendance-records/20/status",
            json={"attendance_status": "invalid", "reason": "Invalid data."},
        )

    assert session.rolled_back is True
    assert attendance.attendance_status == "valid"


def test_update_attendance_status_requires_authentication():
    client = make_client(FakeSession(attendance_record=make_attendance()))

    response = client.patch(
        "/api/attendance-records/20/status",
        json={"attendance_status": "void", "reason": "Invalid submission."},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
