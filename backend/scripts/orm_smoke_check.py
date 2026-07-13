"""Manual ORM smoke check.

Run this kapag gusto mong siguraduhin na ang models ay gumagana sa real MySQL DB.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    AttendanceRecord,
    AttendanceRecordAddress,
    AttendanceSheetExport,
    AuditLog,
    Event,
    OrganizationalUnit,
    PSGCBarangay,
    PSGCCityMunicipality,
    PSGCProvince,
    PSGCRegion,
    Program,
    ProgramAdminAssignment,
    Role,
    User,
)


COUNT_CHECKS: tuple[tuple[str, type[Any]], ...] = (
    # Core table counts muna; mabilis itong signal kung may missing/import issue.
    ("roles", Role),
    ("organizational_units", OrganizationalUnit),
    ("users", User),
    ("programs", Program),
    ("program_admin_assignments", ProgramAdminAssignment),
    ("events", Event),
    ("attendance_records", AttendanceRecord),
    ("attendance_record_addresses", AttendanceRecordAddress),
    ("attendance_sheet_exports", AttendanceSheetExport),
    ("audit_logs", AuditLog),
    ("psgc_regions", PSGCRegion),
    ("psgc_provinces", PSGCProvince),
    ("psgc_cities_municipalities", PSGCCityMunicipality),
    ("psgc_barangays", PSGCBarangay),
)


@dataclass(frozen=True)
class LatestAttendanceRow:
    """Simplified row para readable ang latest attendance output sa terminal."""

    attendance_id: int
    attendee_name: str
    event_code: str
    attendance_status: str
    region_name: str
    province_name: str | None
    city_municipality_name: str
    barangay_name: str


@dataclass(frozen=True)
class ORMSmokeCheckResult:
    """Result object ng smoke check bago siya gawing text report."""

    table_counts: dict[str, int]
    latest_attendance: list[LatestAttendanceRow]


def run_orm_smoke_check(session: Session) -> ORMSmokeCheckResult:
    """Queries core tables and latest attendance rows using ORM relationships."""
    table_counts = {
        table_name: int(session.scalar(select(func.count()).select_from(model)) or 0)
        for table_name, model in COUNT_CHECKS
    }

    latest_attendance_rows = session.execute(
        # Join path: attendance -> event -> address -> PSGC tables.
        select(
            AttendanceRecord.attendance_id,
            AttendanceRecord.first_name,
            AttendanceRecord.last_name,
            Event.event_code,
            AttendanceRecord.attendance_status,
            PSGCRegion.region_name,
            PSGCProvince.province_name,
            PSGCCityMunicipality.city_municipality_name,
            PSGCBarangay.barangay_name,
        )
        .join(AttendanceRecord.event)
        .join(AttendanceRecord.address)
        .join(AttendanceRecordAddress.region)
        .outerjoin(AttendanceRecordAddress.province)
        .join(AttendanceRecordAddress.city_municipality)
        .join(AttendanceRecordAddress.barangay)
        .order_by(AttendanceRecord.submitted_at.desc())
        .limit(5)
    )

    latest_attendance = [
        LatestAttendanceRow(
            attendance_id=row[0],
            attendee_name=f"{row[1]} {row[2]}",
            event_code=row[3],
            attendance_status=row[4],
            region_name=row[5],
            province_name=row[6],
            city_municipality_name=row[7],
            barangay_name=row[8],
        )
        for row in latest_attendance_rows
    ]

    return ORMSmokeCheckResult(
        table_counts=table_counts,
        latest_attendance=latest_attendance,
    )


def format_smoke_check_report(result: ORMSmokeCheckResult) -> str:
    """Ginagawang readable terminal output ang smoke check result."""
    lines = ["ORM smoke check", "", "Table counts:"]

    for table_name, total_rows in result.table_counts.items():
        lines.append(f"- {table_name}: {total_rows}")

    lines.extend(["", "Latest attendance records:"])

    if not result.latest_attendance:
        lines.append("- No attendance records found.")
    else:
        for row in result.latest_attendance:
            province_name = row.province_name or "N/A"
            lines.append(
                "- "
                f"#{row.attendance_id} {row.attendee_name} | "
                f"{row.event_code} | {row.attendance_status} | "
                f"{row.region_name} / {province_name} / "
                f"{row.city_municipality_name} / {row.barangay_name}"
            )

    return "\n".join(lines)


def main() -> None:
    """CLI entry point kapag ni-run via python -m scripts.orm_smoke_check."""
    with SessionLocal() as session:
        result = run_orm_smoke_check(session)

    print(format_smoke_check_report(result))


if __name__ == "__main__":
    main()
