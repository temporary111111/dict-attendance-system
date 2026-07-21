from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import attendance_sheet_service
from app.services.attendance_sheet_pdf import AttendanceSheetPDFError


class FakeSession:
    def __init__(
        self,
        *,
        event=None,
        records=None,
        assignment_id=None,
        fail_flush=False,
        fail_commit=False,
    ):
        self.event = event
        self.records = records or []
        self.assignment_id = assignment_id
        self.fail_flush = fail_flush
        self.fail_commit = fail_commit
        self.statements = []
        self.statement_parameters = []
        self.added_objects = []
        self.flush_count = 0
        self.committed = False
        self.rolled_back = False

    def scalar(self, statement):
        statement_text = str(statement)
        self.statements.append(statement_text)
        self.statement_parameters.append(statement.compile().params)
        if "FROM events" in statement_text:
            return self.event
        if "program_admin_assignments.assignment_id" in statement_text:
            return self.assignment_id
        return None

    def scalars(self, statement):
        self.statements.append(str(statement))
        self.statement_parameters.append(statement.compile().params)
        return SimpleNamespace(all=lambda: self.records)

    def add(self, record):
        self.added_objects.append(record)

    def flush(self):
        self.flush_count += 1
        if self.fail_flush:
            raise RuntimeError("flush failed")
        for record in self.added_objects:
            if record.__class__.__name__ == "AttendanceSheetExport":
                record.export_id = 81

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("commit failed")
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def make_user(role_name="super_admin", user_id=1):
    return SimpleNamespace(
        user_id=user_id,
        role=SimpleNamespace(role_name=role_name),
    )


def make_event(event_status="closed", event_code="EVENT-2026"):
    unit = SimpleNamespace(
        unit_name="DICT Regional Office No. V - Bicol",
        org_unit_id=10,
        parent_unit_id=None,
        parent=None,
    )
    program = SimpleNamespace(
        program_id=3,
        program_name="Free Wi-Fi for All",
        owning_unit=unit,
        logo_path=None,
    )
    return SimpleNamespace(
        event_id=5,
        program_id=3,
        program=program,
        event_title="Digital Inclusion Orientation",
        venue="DICT Regional Office",
        event_date=date(2026, 8, 15),
        event_code=event_code,
        event_status=event_status,
    )


def make_attendance(
    attendance_id=20,
    *,
    signature_text="Maria Santos Reyes",
    signature_image_path=None,
):
    return SimpleNamespace(
        attendance_id=attendance_id,
        first_name="Maria",
        middle_name="Santos",
        last_name="Reyes",
        suffix=None,
        affiliation="Municipality of San Fernando",
        designation_category="Government Official",
        sex="F",
        email="maria.reyes@example.com",
        consent_documentation_publication=False,
        consent_database_processing=True,
        signature_text=signature_text,
        signature_image_path=signature_image_path,
        submitted_at=datetime(2026, 8, 15, 9, 30),
    )


def generate(
    session,
    tmp_path,
    *,
    current_user=None,
):
    return attendance_sheet_service.generate_attendance_sheet_export(
        session,
        5,
        current_user or make_user(),
        logo_path=Path("app/assets/dict-logo.png"),
        program_logo_directory=tmp_path / "program_logos",
        signature_directory=tmp_path / "signatures",
        ip_address="127.0.0.1",
        user_agent="pytest-client",
    )


@pytest.mark.parametrize("event_status", ["draft", "open", "closed", "archived"])
def test_super_admin_can_export_every_event_status(
    event_status,
    tmp_path,
    monkeypatch,
):
    captured = {}

    def fake_render(event, rows, *, logo_path, **kwargs):
        captured["event"] = event
        captured["rows"] = rows
        captured["logo_path"] = logo_path
        return b"%PDF-test"

    monkeypatch.setattr(attendance_sheet_service, "render_attendance_sheet_pdf", fake_render)
    session = FakeSession(
        event=make_event(event_status),
        records=[make_attendance()],
    )

    result = generate(session, tmp_path)

    assert result.pdf_bytes == b"%PDF-test"
    assert result.export.event_id == 5
    assert result.export.exported_by_user_id == 1
    assert result.export.export_format == "pdf"
    assert result.export.file_path is None
    assert result.export.total_records == 1
    assert result.filename == "attendance-sheet-EVENT-2026.pdf"
    assert captured["event"].office_name == "DICT Regional Office No. V - Bicol"
    assert captured["rows"][0].attendee_name == "Maria Santos Reyes"
    assert captured["rows"][0].row_number == 1
    statements = "\n".join(session.statements)
    assert "attendance_status" in statements
    assert any(
        "valid" in parameters.values()
        for parameters in session.statement_parameters
    )
    assert "submitted_at ASC" in statements
    assert "attendance_id ASC" in statements
    assert session.flush_count == 1
    assert session.committed is True
    audit = session.added_objects[-1]
    assert audit.action == "generated_attendance_sheet"
    assert audit.entity_type == "attendance_sheet_export"
    assert audit.entity_id == 81
    assert audit.new_values_json == {
        "event_id": 5,
        "export_format": "pdf",
        "total_records": 1,
        "event_status": event_status,
    }
    assert audit.ip_address == "127.0.0.1"
    assert audit.user_agent == "pytest-client"


def test_assigned_program_admin_can_export(tmp_path, monkeypatch):
    monkeypatch.setattr(
        attendance_sheet_service,
        "render_attendance_sheet_pdf",
        lambda event, rows, *, logo_path, **kwargs: b"%PDF-test",
    )
    session = FakeSession(
        event=make_event("open"),
        records=[make_attendance()],
        assignment_id=14,
    )

    result = generate(
        session,
        tmp_path,
        current_user=make_user("program_admin", user_id=2),
    )

    assert result.export.exported_by_user_id == 2
    assert any("assignment_status" in statement for statement in session.statements)


def test_unassigned_program_admin_cannot_export(tmp_path):
    session = FakeSession(event=make_event())

    with pytest.raises(attendance_sheet_service.AttendanceSheetAccessDeniedError):
        generate(
            session,
            tmp_path,
            current_user=make_user("program_admin", user_id=2),
        )

    assert session.added_objects == []


def test_missing_event_cannot_export(tmp_path):
    with pytest.raises(attendance_sheet_service.AttendanceSheetEventNotFoundError):
        generate(FakeSession(), tmp_path)


def test_service_safely_resolves_signature_image(tmp_path, monkeypatch):
    signature_directory = tmp_path / "signatures"
    image_path = signature_directory / "event-5" / "signature.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"safe-png-placeholder")
    captured = {}

    def fake_render(event, rows, *, logo_path, **kwargs):
        captured["row"] = rows[0]
        return b"%PDF-test"

    monkeypatch.setattr(attendance_sheet_service, "render_attendance_sheet_pdf", fake_render)
    session = FakeSession(
        event=make_event(),
        records=[
            make_attendance(
                signature_text=None,
                signature_image_path="event-5/signature.png",
            )
        ],
    )

    generate(session, tmp_path)

    assert captured["row"].signature_image_path == image_path.resolve()


def test_renderer_failure_writes_no_history(tmp_path, monkeypatch):
    def fail_render(event, rows, *, logo_path, **kwargs):
        raise AttendanceSheetPDFError

    monkeypatch.setattr(attendance_sheet_service, "render_attendance_sheet_pdf", fail_render)
    session = FakeSession(event=make_event(), records=[make_attendance()])

    with pytest.raises(attendance_sheet_service.AttendanceSheetGenerationError):
        generate(session, tmp_path)

    assert session.added_objects == []
    assert session.committed is False


@pytest.mark.parametrize("failure", ["flush", "commit"])
def test_history_failure_rolls_back(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(
        attendance_sheet_service,
        "render_attendance_sheet_pdf",
        lambda event, rows, *, logo_path, **kwargs: b"%PDF-test",
    )
    session = FakeSession(
        event=make_event(),
        records=[make_attendance()],
        fail_flush=failure == "flush",
        fail_commit=failure == "commit",
    )

    with pytest.raises(
        attendance_sheet_service.AttendanceSheetExportPersistenceError
    ):
        generate(session, tmp_path)

    assert session.rolled_back is True


def test_filename_sanitizes_unsafe_event_code(tmp_path, monkeypatch):
    monkeypatch.setattr(
        attendance_sheet_service,
        "render_attendance_sheet_pdf",
        lambda event, rows, *, logo_path, **kwargs: b"%PDF-test",
    )
    session = FakeSession(event=make_event(event_code="Event / Orientation 2026"))

    result = generate(session, tmp_path)

    assert result.filename == "attendance-sheet-Event-Orientation-2026.pdf"
