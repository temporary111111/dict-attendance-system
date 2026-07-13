from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app


class FakeSession:
    def __init__(
        self,
        *,
        listed_events=None,
        events=None,
        programs=None,
        assignment_visibility_id=None,
        existing_event_code_id=None,
    ):
        self.listed_events = listed_events or []
        self.events = events or {}
        self.programs = programs or {}
        self.assignment_visibility_id = assignment_visibility_id
        self.existing_event_code_id = existing_event_code_id
        self.scalars_statements = []
        self.added_event = None
        self.committed = False

    def scalars(self, statement):
        self.scalars_statements.append(str(statement))
        return SimpleNamespace(all=lambda: self.listed_events)

    def scalar(self, statement):
        statement_text = str(statement)
        if "program_admin_assignments.assignment_id" in statement_text:
            return self.assignment_visibility_id
        if "events.event_code" in statement_text:
            return self.existing_event_code_id
        return None

    def get(self, model, key):
        if model.__name__ == "Event":
            return self.events.get(key)
        if model.__name__ == "Program":
            return self.programs.get(key)
        return None

    def add(self, event):
        self.added_event = event

    def commit(self):
        self.committed = True

    def rollback(self):
        self.committed = False

    def refresh(self, event):
        if getattr(event, "event_id", None) is None:
            event.event_id = 12


def make_settings(qr_directory: Path | None = None) -> Settings:
    settings_data = {
        "jwt_secret_key": "test-secret-key-with-more-than-32-bytes",
        "public_attendance_url_template": (
            "http://frontend.example.test/attendance.html?event={event_code}"
        ),
    }
    if qr_directory is not None:
        settings_data["qr_code_directory"] = qr_directory
    return Settings(**settings_data)


def make_user(role_name="super_admin", user_id=1):
    return SimpleNamespace(
        user_id=user_id,
        role=SimpleNamespace(role_name=role_name, is_active=True),
        account_status="active",
    )


def make_program(program_id=3, *, status="active"):
    return SimpleNamespace(
        program_id=program_id,
        program_name="Free Wi-Fi for All",
        program_status=status,
    )


def make_event(
    event_id=5,
    *,
    program=None,
    event_status="draft",
    public_attendance_url=None,
    qr_code_path=None,
    opened_at=None,
    closed_at=None,
):
    event_program = program or make_program()
    return SimpleNamespace(
        event_id=event_id,
        program_id=event_program.program_id,
        program=event_program,
        created_by_user_id=2,
        event_title="Digital Inclusion Orientation",
        event_description="Community orientation.",
        venue="DICT Regional Office",
        event_date=date(2026, 8, 15),
        event_code="old-event-code",
        public_attendance_url=public_attendance_url,
        qr_code_path=qr_code_path,
        event_status=event_status,
        opened_at=opened_at,
        closed_at=closed_at,
    )


def make_client(
    session,
    *,
    current_user=None,
    qr_directory=None,
) -> TestClient:
    app = create_app(make_settings(qr_directory))

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return TestClient(app)


def valid_event_payload() -> dict:
    return {
        "event_title": "  Digital Inclusion Orientation  ",
        "event_description": "  Community orientation.  ",
        "venue": "  DICT Regional Office  ",
        "event_date": "2026-08-15",
    }


def test_list_events_returns_non_archived_events_for_super_admin():
    session = FakeSession(listed_events=[make_event()])
    client = make_client(session, current_user=make_user())

    response = client.get("/api/events")

    assert response.status_code == 200
    assert response.json()["data"][0] == {
        "event_id": 5,
        "program": {
            "program_id": 3,
            "program_name": "Free Wi-Fi for All",
        },
        "created_by_user_id": 2,
        "event_title": "Digital Inclusion Orientation",
        "event_description": "Community orientation.",
        "venue": "DICT Regional Office",
        "event_date": "2026-08-15",
        "event_code": "old-event-code",
        "public_attendance_url": None,
        "qr_code_path": None,
        "event_status": "draft",
        "opened_at": None,
        "closed_at": None,
    }
    assert "event_status" in session.scalars_statements[0]


def test_list_events_filters_active_assignments_for_program_admin():
    session = FakeSession(listed_events=[make_event()])
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.get("/api/events")

    assert response.status_code == 200
    assert "program_admin_assignments" in session.scalars_statements[0]
    assert "assignment_status" in session.scalars_statements[0]


def test_create_event_generates_code_and_saves_draft_for_assigned_admin():
    program = make_program()
    session = FakeSession(
        programs={3: program},
        assignment_visibility_id=10,
    )
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.post("/api/programs/3/events", json=valid_event_payload())

    assert response.status_code == 201
    assert response.json()["data"]["event_id"] == 12
    assert response.json()["data"]["event_status"] == "draft"
    assert response.json()["data"]["event_code"]
    assert session.added_event.created_by_user_id == 2
    assert session.added_event.public_attendance_url is None
    assert session.committed is True


def test_create_event_rejects_unassigned_program_admin():
    session = FakeSession(programs={3: make_program()})
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.post("/api/programs/3/events", json=valid_event_payload())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_create_event_rejects_archived_program():
    session = FakeSession(programs={3: make_program(status="archived")})
    client = make_client(session, current_user=make_user())

    response = client.post("/api/programs/3/events", json=valid_event_payload())

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROGRAM_ARCHIVED"


def test_get_event_allows_assigned_program_admin():
    session = FakeSession(
        events={5: make_event()},
        assignment_visibility_id=10,
    )
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.get("/api/events/5")

    assert response.status_code == 200
    assert response.json()["data"]["event_id"] == 5


def test_get_event_rejects_unassigned_program_admin():
    session = FakeSession(events={5: make_event()})
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.get("/api/events/5")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_update_event_changes_fields_and_clears_description():
    event = make_event()
    session = FakeSession(events={5: event})
    client = make_client(session, current_user=make_user())

    response = client.patch(
        "/api/events/5",
        json={
            "event_title": "  Updated Orientation  ",
            "event_description": None,
            "venue": "  New Venue  ",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["event_title"] == "Updated Orientation"
    assert response.json()["data"]["event_description"] is None
    assert response.json()["data"]["venue"] == "New Venue"


def test_update_event_rejects_archived_event():
    session = FakeSession(events={5: make_event(event_status="archived")})
    client = make_client(session, current_user=make_user())

    response = client.patch("/api/events/5", json={"venue": "New Venue"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVENT_ARCHIVED"


def test_update_event_rejects_empty_payload():
    session = FakeSession(events={5: make_event()})
    client = make_client(session, current_user=make_user())

    response = client.patch("/api/events/5", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_refresh_attendance_link_rotates_code_and_writes_qr_png(tmp_path):
    event = make_event()
    session = FakeSession(events={5: event})
    client = make_client(
        session,
        current_user=make_user(),
        qr_directory=tmp_path,
    )

    response = client.post("/api/events/5/attendance-link")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["event_code"] != "old-event-code"
    assert data["event_code"] in data["public_attendance_url"]
    assert data["qr_code_path"].startswith("/media/qr-codes/")
    qr_file = tmp_path / Path(data["qr_code_path"]).name
    assert qr_file.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    qr_response = client.get(data["qr_code_path"])
    assert qr_response.status_code == 200
    assert qr_response.headers["content-type"] == "image/png"


def test_open_event_requires_generated_attendance_link():
    session = FakeSession(events={5: make_event()})
    client = make_client(session, current_user=make_user())

    response = client.post("/api/events/5/open")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ATTENDANCE_LINK_REQUIRED"


def test_open_event_rejects_archived_parent_program():
    program = make_program(status="archived")
    event = make_event(
        program=program,
        public_attendance_url="http://frontend/event",
        qr_code_path="/media/qr-codes/event.png",
    )
    session = FakeSession(events={5: event})
    client = make_client(session, current_user=make_user())

    response = client.post("/api/events/5/open")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROGRAM_ARCHIVED"


def test_open_and_close_event_records_status_timestamps():
    event = make_event(
        public_attendance_url="http://frontend/event",
        qr_code_path="/media/qr-codes/event.png",
    )
    session = FakeSession(events={5: event})
    client = make_client(session, current_user=make_user())

    open_response = client.post("/api/events/5/open")
    close_response = client.post("/api/events/5/close")

    assert open_response.status_code == 200
    assert open_response.json()["data"]["event_status"] == "open"
    assert event.opened_at is not None
    assert close_response.status_code == 200
    assert close_response.json()["data"]["event_status"] == "closed"
    assert event.closed_at is not None


def test_reopen_closed_event_clears_closed_timestamp():
    event = make_event(
        event_status="closed",
        public_attendance_url="http://frontend/event",
        qr_code_path="/media/qr-codes/event.png",
        opened_at=datetime(2026, 8, 15, 9, 0, 0),
        closed_at=datetime(2026, 8, 15, 17, 0, 0),
    )
    session = FakeSession(events={5: event})
    client = make_client(session, current_user=make_user())

    response = client.post("/api/events/5/open")

    assert response.status_code == 200
    assert response.json()["data"]["event_status"] == "open"
    assert event.closed_at is None


def test_close_event_rejects_draft_status():
    session = FakeSession(events={5: make_event()})
    client = make_client(session, current_user=make_user())

    response = client.post("/api/events/5/close")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_EVENT_TRANSITION"


def test_archive_event_requires_open_event_to_be_closed_first():
    session = FakeSession(events={5: make_event(event_status="open")})
    client = make_client(session, current_user=make_user())

    response = client.patch("/api/events/5/archive")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVENT_MUST_BE_CLOSED"


def test_archive_event_soft_archives_draft_event():
    event = make_event()
    session = FakeSession(events={5: event})
    client = make_client(session, current_user=make_user())

    response = client.patch("/api/events/5/archive")

    assert response.status_code == 200
    assert response.json()["data"]["event_status"] == "archived"
    assert event.event_status == "archived"


def test_archive_event_requires_super_admin():
    session = FakeSession(
        events={5: make_event()},
        assignment_visibility_id=10,
    )
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.patch("/api/events/5/archive")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_event_routes_require_authentication():
    client = make_client(FakeSession())

    response = client.get("/api/events")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
