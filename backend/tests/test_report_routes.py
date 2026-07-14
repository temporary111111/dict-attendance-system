from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.api import reports as reports_api
from app.db.session import get_db
from app.main import create_app
from app.services.report_service import (
    InvalidReportDateRangeError,
    ReportAccessDeniedError,
    ReportEventNotFoundError,
    get_dashboard_summary,
    get_program_summary,
)


def make_user(role_name="super_admin", user_id=1):
    return SimpleNamespace(
        user_id=user_id,
        role=SimpleNamespace(role_name=role_name, is_active=True),
        account_status="active",
    )


def make_client(*, current_user=None):
    app = create_app()

    def override_get_db():
        yield SimpleNamespace()

    app.dependency_overrides[get_db] = override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return TestClient(app)


def dashboard_data():
    return {
        "totals": {"programs": 2, "events": 3, "attendance_records": 8},
        "events_by_status": {
            "draft": 1,
            "open": 1,
            "closed": 1,
            "archived": 0,
        },
        "attendance_by_status": {
            "valid": 6,
            "duplicate": 1,
            "invalid": 1,
            "void": 0,
        },
        "recent_events": [
            {
                "event_id": 5,
                "program_id": 3,
                "program_name": "Free Wi-Fi for All",
                "event_title": "Digital Inclusion Orientation",
                "event_date": date(2026, 8, 15),
                "event_status": "open",
                "total_attendance": 8,
                "valid_attendance": 6,
            }
        ],
    }


def test_dashboard_summary_returns_role_scoped_aggregates(monkeypatch):
    monkeypatch.setattr(
        reports_api,
        "get_dashboard_summary",
        lambda db, current_user: dashboard_data(),
    )
    client = make_client(current_user=make_user())

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json()["data"]["totals"] == {
        "programs": 2,
        "events": 3,
        "attendance_records": 8,
    }
    assert response.json()["data"]["recent_events"][0]["event_id"] == 5


def test_program_summary_passes_date_filters(monkeypatch):
    captured = {}

    def fake_summary(db, program_id, current_user, *, date_from, date_to):
        captured.update(
            program_id=program_id,
            date_from=date_from,
            date_to=date_to,
        )
        return {
            "program_id": program_id,
            "program_name": "Free Wi-Fi for All",
            "program_status": "active",
            "date_range": {"date_from": date_from, "date_to": date_to},
            "total_events": 1,
            "total_attendance": 8,
            "events_by_status": {
                "draft": 0,
                "open": 1,
                "closed": 0,
                "archived": 0,
            },
            "attendance_by_status": {
                "valid": 6,
                "duplicate": 1,
                "invalid": 1,
                "void": 0,
            },
            "events": [
                {
                    "event_id": 5,
                    "event_title": "Digital Inclusion Orientation",
                    "event_date": date(2026, 8, 15),
                    "event_status": "open",
                    "total_attendance": 8,
                    "valid_attendance": 6,
                }
            ],
        }

    monkeypatch.setattr(reports_api, "get_program_summary", fake_summary)
    client = make_client(current_user=make_user("program_admin"))

    response = client.get(
        "/api/reports/programs/3/summary"
        "?dateFrom=2026-08-01&dateTo=2026-08-31"
    )

    assert response.status_code == 200
    assert captured == {
        "program_id": 3,
        "date_from": date(2026, 8, 1),
        "date_to": date(2026, 8, 31),
    }
    assert response.json()["data"]["total_attendance"] == 8


def test_program_summary_maps_invalid_date_range(monkeypatch):
    def fail(*args, **kwargs):
        raise InvalidReportDateRangeError

    monkeypatch.setattr(reports_api, "get_program_summary", fail)
    client = make_client(current_user=make_user())

    response = client.get(
        "/api/reports/programs/3/summary"
        "?dateFrom=2026-09-01&dateTo=2026-08-01"
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_event_report_returns_breakdowns(monkeypatch):
    monkeypatch.setattr(
        reports_api,
        "get_event_attendance_report",
        lambda db, event_id, current_user: {
            "event_id": event_id,
            "event_title": "Digital Inclusion Orientation",
            "event_date": date(2026, 8, 15),
            "venue": "DICT Regional Office",
            "event_status": "closed",
            "program_id": 3,
            "program_name": "Free Wi-Fi for All",
            "total_attendance": 8,
            "attendance_by_status": {
                "valid": 6,
                "duplicate": 1,
                "invalid": 1,
                "void": 0,
            },
            "attendees_by_sex": {
                "female": 4,
                "male": 3,
                "unspecified": 1,
            },
            "documentation_consent": {"accepted": 5, "declined": 3},
        },
    )
    client = make_client(current_user=make_user())

    response = client.get("/api/reports/events/5/attendance")

    assert response.status_code == 200
    assert response.json()["data"]["attendance_by_status"]["valid"] == 6
    assert response.json()["data"]["attendees_by_sex"]["unspecified"] == 1


@pytest.mark.parametrize(
    ("error", "status_code", "code"),
    [
        (ReportEventNotFoundError(), 404, "EVENT_NOT_FOUND"),
        (ReportAccessDeniedError(), 403, "FORBIDDEN"),
    ],
)
def test_event_report_maps_access_errors(monkeypatch, error, status_code, code):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(reports_api, "get_event_attendance_report", fail)
    client = make_client(current_user=make_user("program_admin"))

    response = client.get("/api/reports/events/5/attendance")

    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


class EmptyAggregateSession:
    def __init__(self):
        self.statements = []

    def scalar(self, statement):
        self.statements.append(str(statement))
        return 0

    def execute(self, statement):
        self.statements.append(str(statement))
        return SimpleNamespace(all=lambda: [])


def test_program_admin_dashboard_queries_use_active_assignments():
    session = EmptyAggregateSession()

    result = get_dashboard_summary(session, make_user("program_admin", user_id=9))

    assert result["totals"] == {
        "programs": 0,
        "events": 0,
        "attendance_records": 0,
    }
    assert session.statements
    assert all("program_admin_assignments" in sql for sql in session.statements)
    assert all("assignment_status" in sql for sql in session.statements)


def test_program_report_rejects_reversed_dates_before_querying_database():
    with pytest.raises(InvalidReportDateRangeError):
        get_program_summary(
            SimpleNamespace(),
            3,
            make_user(),
            date_from=date(2026, 9, 1),
            date_to=date(2026, 8, 1),
        )
