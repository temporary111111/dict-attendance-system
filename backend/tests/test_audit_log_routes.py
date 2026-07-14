from datetime import date, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user, require_super_admin
from app.db.session import get_db
from app.main import create_app


class FakeSession:
    def __init__(self, *, items=None, total_items=0):
        self.items = items or []
        self.total_items = total_items
        self.statements = []

    def scalar(self, statement):
        self.statements.append(str(statement))
        return self.total_items

    def scalars(self, statement):
        self.statements.append(str(statement))
        return SimpleNamespace(all=lambda: self.items)


def make_log(*, audit_log_id=12, user=None):
    return SimpleNamespace(
        audit_log_id=audit_log_id,
        user=user,
        action="attendance_status_changed",
        entity_type="attendance_record",
        entity_id=20,
        description="Attendance status changed from valid to void.",
        old_values_json={"attendance_status": "valid"},
        new_values_json={
            "attendance_status": "void",
            "reason": "Wrong attendee email.",
        },
        ip_address="127.0.0.1",
        user_agent="pytest",
        created_at=datetime(2026, 8, 15, 10, 30),
    )


def make_client(session, *, super_admin=True, program_admin=False):
    app = create_app()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    if super_admin:
        app.dependency_overrides[require_super_admin] = lambda: SimpleNamespace(
            user_id=1
        )
    elif program_admin:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            user_id=2,
            role=SimpleNamespace(role_name="program_admin", is_active=True),
            account_status="active",
        )
    return TestClient(app)


def test_list_audit_logs_returns_actor_values_and_pagination():
    actor = SimpleNamespace(user_id=1, full_name="System Administrator")
    session = FakeSession(items=[make_log(user=actor)], total_items=26)
    client = make_client(session)

    response = client.get("/api/audit-logs?page=2&pageSize=10")

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "items": [
                {
                    "audit_log_id": 12,
                    "actor": {
                        "user_id": 1,
                        "full_name": "System Administrator",
                    },
                    "action": "attendance_status_changed",
                    "entity_type": "attendance_record",
                    "entity_id": 20,
                    "description": (
                        "Attendance status changed from valid to void."
                    ),
                    "old_values": {"attendance_status": "valid"},
                    "new_values": {
                        "attendance_status": "void",
                        "reason": "Wrong attendee email.",
                    },
                    "ip_address": "127.0.0.1",
                    "user_agent": "pytest",
                    "created_at": "2026-08-15T10:30:00",
                }
            ],
            "pagination": {
                "page": 2,
                "page_size": 10,
                "total_items": 26,
                "total_pages": 3,
            },
        },
        "message": "Audit logs retrieved.",
    }


def test_list_audit_logs_keeps_deleted_actor_as_null():
    session = FakeSession(items=[make_log(user=None)], total_items=1)
    client = make_client(session)

    response = client.get("/api/audit-logs")

    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["actor"] is None


def test_list_audit_logs_applies_supported_filters():
    session = FakeSession(total_items=0)
    client = make_client(session)

    response = client.get(
        "/api/audit-logs?userId=3"
        "&action=attendance_status_changed"
        "&entityType=attendance_record"
        "&entityId=20"
        "&dateFrom=2026-08-01"
        "&dateTo=2026-08-31"
        "&search=void"
    )

    assert response.status_code == 200
    assert len(session.statements) == 2
    for statement in session.statements:
        assert "audit_logs.user_id" in statement
        assert "audit_logs.action" in statement
        assert "audit_logs.entity_type" in statement
        assert "audit_logs.entity_id" in statement
        assert "audit_logs.created_at" in statement
        assert "lower(audit_logs.description)" in statement
        assert "lower(users.full_name)" in statement


def test_list_audit_logs_rejects_reversed_date_range():
    client = make_client(FakeSession())

    response = client.get(
        "/api/audit-logs?dateFrom=2026-09-01&dateTo=2026-08-01"
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_list_audit_logs_rejects_invalid_pagination():
    client = make_client(FakeSession())

    response = client.get("/api/audit-logs?page=0&pageSize=101")

    assert response.status_code == 422


def test_program_admin_cannot_view_audit_logs():
    client = make_client(
        FakeSession(),
        super_admin=False,
        program_admin=True,
    )

    response = client.get("/api/audit-logs")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_audit_log_date_to_accepts_maximum_date():
    session = FakeSession()
    client = make_client(session)

    response = client.get(
        f"/api/audit-logs?dateFrom={date.max.isoformat()}"
        f"&dateTo={date.max.isoformat()}"
    )

    assert response.status_code == 200
