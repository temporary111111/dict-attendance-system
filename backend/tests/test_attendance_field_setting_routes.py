from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app
from app.models import AuditLog


FIELD_DEFINITIONS = [
    ("first_name", "First name", True, False),
    ("middle_name", "Middle name", False, True),
    ("last_name", "Last name", True, False),
    ("suffix", "Suffix", False, True),
    ("affiliation", "Affiliation", True, True),
    ("designation_category", "Designation/category", True, True),
    ("sex", "Sex", True, True),
    ("email", "Email", True, False),
    (
        "consent_documentation_publication",
        "Documentation/publication consent",
        True,
        True,
    ),
    (
        "consent_database_processing",
        "Database-processing consent",
        True,
        False,
    ),
    ("signature", "Signature", False, True),
    ("psgc_address", "PSGC address", False, True),
    ("street_address", "Street address", False, True),
    ("postal_code", "Postal code", False, True),
]


def make_event(*, status="draft"):
    settings = []
    for order, (key, label, required, configurable) in enumerate(
        FIELD_DEFINITIONS,
        start=1,
    ):
        field = SimpleNamespace(
            field_key=key,
            field_label=label,
            default_is_required=required,
            is_admin_configurable=configurable,
            display_order=order,
        )
        settings.append(
            SimpleNamespace(
                event_id=5,
                field_key=key,
                is_required=required,
                is_visible=True,
                field=field,
            )
        )
    return SimpleNamespace(
        event_id=5,
        program_id=3,
        event_status=status,
        attendance_field_settings=settings,
    )


class FakeSession:
    def __init__(
        self,
        *,
        event=None,
        assignment_id=10,
        fail_commit=False,
    ):
        self.event = event
        self.assignment_id = assignment_id
        self.fail_commit = fail_commit
        self.added_objects = []
        self.committed = False
        self.rolled_back = False

    def get(self, model, key):
        if model.__name__ == "Event" and key == 5:
            return self.event
        return None

    def scalar(self, statement):
        if "program_admin_assignments.assignment_id" in str(statement):
            return self.assignment_id
        return None

    def add(self, value):
        self.added_objects.append(value)

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("database failed")
        self.committed = True

    def rollback(self):
        self.rolled_back = True
        self.committed = False


def make_user(role="super_admin", user_id=1):
    return SimpleNamespace(
        user_id=user_id,
        role=SimpleNamespace(role_name=role, is_active=True),
        account_status="active",
    )


def make_client(session, *, user=None):
    app = create_app(
        Settings(jwt_secret_key="test-secret-key-with-more-than-32-bytes")
    )

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user or make_user()
    return TestClient(app, raise_server_exceptions=False)


def requirement_map(response):
    return {
        item["field_key"]: item["is_required"]
        for item in response.json()["data"]
    }


def visibility_map(response):
    return {
        item["field_key"]: item["is_visible"]
        for item in response.json()["data"]
    }


def test_get_event_attendance_field_settings_returns_ordered_fixed_fields():
    client = make_client(FakeSession(event=make_event()))

    response = client.get("/api/events/5/attendance-field-settings")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 14
    assert data[0] == {
        "field_key": "first_name",
        "field_label": "First name",
        "is_required": True,
        "is_visible": True,
        "is_admin_configurable": False,
        "display_order": 1,
    }
    assert data[-1]["field_key"] == "postal_code"


def test_assigned_program_admin_updates_configurable_requirements_atomically():
    event = make_event(status="open")
    session = FakeSession(event=event, assignment_id=22)
    client = make_client(session, user=make_user("program_admin", user_id=8))

    response = client.patch(
        "/api/events/5/attendance-field-settings",
        json={"requirements": {"affiliation": False, "signature": True}},
        headers={"user-agent": "pytest-admin"},
    )

    assert response.status_code == 200
    assert requirement_map(response)["affiliation"] is False
    assert requirement_map(response)["signature"] is True
    audit = next(item for item in session.added_objects if isinstance(item, AuditLog))
    assert audit.action == "updated_attendance_field_requirements"
    assert audit.entity_type == "event"
    assert audit.entity_id == 5
    assert audit.old_values_json == {"affiliation": True, "signature": False}
    assert audit.new_values_json == {"affiliation": False, "signature": True}
    assert session.committed is True


def test_update_rejects_locked_field():
    client = make_client(FakeSession(event=make_event()))

    response = client.patch(
        "/api/events/5/attendance-field-settings",
        json={"requirements": {"email": False}},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "FIELD_NOT_CONFIGURABLE"


def test_hiding_configurable_field_also_makes_it_optional():
    event = make_event()
    event.attendance_field_settings[4].is_required = True
    client = make_client(FakeSession(event=event))

    response = client.patch(
        "/api/events/5/attendance-field-settings",
        json={"visibility": {"affiliation": False}},
    )

    assert response.status_code == 200
    assert visibility_map(response)["affiliation"] is False
    assert requirement_map(response)["affiliation"] is False


def test_hiding_psgc_address_also_hides_dependent_address_fields():
    client = make_client(FakeSession(event=make_event()))

    response = client.patch(
        "/api/events/5/attendance-field-settings",
        json={"visibility": {"psgc_address": False}},
    )

    assert response.status_code == 200
    visibility = visibility_map(response)
    assert visibility["psgc_address"] is False
    assert visibility["street_address"] is False
    assert visibility["postal_code"] is False


def test_update_rejects_hiding_locked_field():
    client = make_client(FakeSession(event=make_event()))

    response = client.patch(
        "/api/events/5/attendance-field-settings",
        json={"visibility": {"email": False}},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "FIELD_NOT_CONFIGURABLE"


def test_update_rejects_street_required_without_psgc_address():
    client = make_client(FakeSession(event=make_event()))

    response = client.patch(
        "/api/events/5/attendance-field-settings",
        json={"requirements": {"street_address": True}},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_FIELD_REQUIREMENTS"


def test_update_rejects_closed_event():
    client = make_client(FakeSession(event=make_event(status="closed")))

    response = client.patch(
        "/api/events/5/attendance-field-settings",
        json={"requirements": {"signature": True}},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "FIELD_SETTINGS_LOCKED"


def test_unassigned_program_admin_cannot_read_settings():
    client = make_client(
        FakeSession(event=make_event(), assignment_id=None),
        user=make_user("program_admin", user_id=8),
    )

    response = client.get("/api/events/5/attendance-field-settings")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_repeating_current_requirement_does_not_commit_or_audit():
    session = FakeSession(event=make_event())
    client = make_client(session)

    response = client.patch(
        "/api/events/5/attendance-field-settings",
        json={"requirements": {"signature": False}},
    )

    assert response.status_code == 200
    assert session.added_objects == []
    assert session.committed is False


def test_failed_update_rolls_back_values_and_audit():
    event = make_event()
    session = FakeSession(event=event, fail_commit=True)
    client = make_client(session)

    response = client.patch(
        "/api/events/5/attendance-field-settings",
        json={"requirements": {"signature": True}},
    )

    assert response.status_code == 500
    assert requirement_map(
        SimpleNamespace(json=lambda: {"data": [
            {
                "field_key": setting.field_key,
                "is_required": setting.is_required,
            }
            for setting in event.attendance_field_settings
        ]})
    )["signature"] is False
    assert session.rolled_back is True
