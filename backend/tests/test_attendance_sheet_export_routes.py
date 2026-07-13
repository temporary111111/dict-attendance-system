from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app
from app.services import attendance_sheet_service
from app.services.attendance_sheet_pdf import AttendanceSheetPDFError


class FakeSession:
    def __init__(
        self,
        *,
        event=None,
        assignment_id=None,
        fail_commit=False,
    ):
        self.event = event
        self.assignment_id = assignment_id
        self.fail_commit = fail_commit
        self.added_objects = []
        self.rolled_back = False

    def scalar(self, statement):
        statement_text = str(statement)
        if "FROM events" in statement_text:
            return self.event
        if "program_admin_assignments.assignment_id" in statement_text:
            return self.assignment_id
        return None

    def scalars(self, statement):
        return SimpleNamespace(all=lambda: [])

    def add(self, record):
        self.added_objects.append(record)

    def flush(self):
        for record in self.added_objects:
            if record.__class__.__name__ == "AttendanceSheetExport":
                record.export_id = 91

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("commit failed")

    def rollback(self):
        self.rolled_back = True


def make_event(event_status="open"):
    return SimpleNamespace(
        event_id=5,
        program_id=3,
        program=SimpleNamespace(
            owning_unit=SimpleNamespace(
                unit_name="DICT Regional Office No. V - Bicol"
            )
        ),
        event_title="Digital Inclusion Orientation",
        venue="DICT Regional Office",
        event_date=date(2026, 8, 15),
        event_code="EVENT-2026",
        event_status=event_status,
    )


def make_user(role_name="super_admin", user_id=1):
    return SimpleNamespace(
        user_id=user_id,
        role=SimpleNamespace(role_name=role_name, is_active=True),
        account_status="active",
    )


def make_client(session, *, current_user=None, signature_directory=None):
    settings = Settings(
        jwt_secret_key="test-secret-key-with-more-than-32-bytes",
        signature_directory=signature_directory or "storage/signatures",
    )
    app = create_app(settings)

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return TestClient(app, raise_server_exceptions=False)


def test_export_route_returns_private_pdf_attachment(tmp_path, monkeypatch):
    monkeypatch.setattr(
        attendance_sheet_service,
        "render_attendance_sheet_pdf",
        lambda event, rows, *, logo_path: b"%PDF-route-test",
    )
    client = make_client(
        FakeSession(event=make_event("draft")),
        current_user=make_user(),
        signature_directory=tmp_path / "signatures",
    )

    response = client.post("/api/events/5/attendance-sheet-exports")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["content-disposition"] == (
        'attachment; filename="attendance-sheet-EVENT-2026.pdf"'
    )
    assert response.content == b"%PDF-route-test"


def test_export_route_requires_authentication():
    client = make_client(FakeSession(event=make_event()))

    response = client.post("/api/events/5/attendance-sheet-exports")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_export_route_returns_event_not_found():
    client = make_client(FakeSession(), current_user=make_user())

    response = client.post("/api/events/999/attendance-sheet-exports")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVENT_NOT_FOUND"


def test_export_route_rejects_unassigned_program_admin():
    client = make_client(
        FakeSession(event=make_event()),
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.post("/api/events/5/attendance-sheet-exports")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_export_route_allows_assigned_program_admin(tmp_path, monkeypatch):
    monkeypatch.setattr(
        attendance_sheet_service,
        "render_attendance_sheet_pdf",
        lambda event, rows, *, logo_path: b"%PDF-assigned",
    )
    client = make_client(
        FakeSession(event=make_event("archived"), assignment_id=17),
        current_user=make_user("program_admin", user_id=2),
        signature_directory=tmp_path / "signatures",
    )

    response = client.post("/api/events/5/attendance-sheet-exports")

    assert response.status_code == 200
    assert response.content == b"%PDF-assigned"


def test_export_route_maps_pdf_generation_failure(monkeypatch):
    def fail_render(event, rows, *, logo_path):
        raise AttendanceSheetPDFError

    monkeypatch.setattr(
        attendance_sheet_service,
        "render_attendance_sheet_pdf",
        fail_render,
    )
    client = make_client(
        FakeSession(event=make_event()),
        current_user=make_user(),
    )

    response = client.post("/api/events/5/attendance-sheet-exports")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == (
        "ATTENDANCE_SHEET_GENERATION_FAILED"
    )


def test_export_route_maps_persistence_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(
        attendance_sheet_service,
        "render_attendance_sheet_pdf",
        lambda event, rows, *, logo_path: b"%PDF-test",
    )
    session = FakeSession(event=make_event(), fail_commit=True)
    client = make_client(
        session,
        current_user=make_user(),
        signature_directory=tmp_path / "signatures",
    )

    response = client.post("/api/events/5/attendance-sheet-exports")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "ATTENDANCE_SHEET_EXPORT_FAILED"
    assert session.rolled_back is True
