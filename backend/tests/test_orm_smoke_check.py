from scripts.orm_smoke_check import (
    COUNT_CHECKS,
    format_smoke_check_report,
    run_orm_smoke_check,
)


class FakeSession:
    def __init__(self):
        self.scalar_calls = 0
        self.execute_calls = 0

    def scalar(self, statement):
        self.scalar_calls += 1
        return self.scalar_calls

    def execute(self, statement):
        self.execute_calls += 1
        return [
            (
                1,
                "Maria",
                "Reyes",
                "SMOKE-TEST-ORIENTATION",
                "valid",
                "Region III (Central Luzon)",
                "Pampanga",
                "City of San Fernando",
                "San Agustin",
            )
        ]


def test_smoke_check_counts_all_core_tables_and_latest_attendance():
    session = FakeSession()

    result = run_orm_smoke_check(session)

    assert session.scalar_calls == len(COUNT_CHECKS)
    assert session.execute_calls == 1
    assert result.table_counts["roles"] == 1
    assert result.table_counts["attendance_form_fields"] == 7
    assert result.table_counts["event_attendance_field_settings"] == 8
    assert result.table_counts["attendance_records"] == 9
    assert result.latest_attendance[0].event_code == "SMOKE-TEST-ORIENTATION"
    assert result.latest_attendance[0].attendee_name == "Maria Reyes"


def test_format_smoke_check_report_includes_counts_and_latest_attendance():
    session = FakeSession()

    result = run_orm_smoke_check(session)
    report = format_smoke_check_report(result)

    assert "ORM smoke check" in report
    assert "roles: 1" in report
    assert "attendance_form_fields: 7" in report
    assert "event_attendance_field_settings: 8" in report
    assert "attendance_records: 9" in report
    assert "Maria Reyes" in report
    assert "Region III (Central Luzon)" in report
