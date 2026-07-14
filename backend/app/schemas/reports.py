"""Response contracts para sa dashboard at summary reports."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class AttendanceStatusCounts(BaseModel):
    valid: int
    duplicate: int
    invalid: int
    void: int


class EventStatusCounts(BaseModel):
    draft: int
    open: int
    closed: int
    archived: int


class DashboardTotals(BaseModel):
    programs: int
    events: int
    attendance_records: int


class RecentEventSummary(BaseModel):
    event_id: int
    program_id: int
    program_name: str
    event_title: str
    event_date: date
    event_status: Literal["draft", "open", "closed", "archived"]
    total_attendance: int
    valid_attendance: int


class DashboardSummaryData(BaseModel):
    totals: DashboardTotals
    events_by_status: EventStatusCounts
    attendance_by_status: AttendanceStatusCounts
    recent_events: list[RecentEventSummary]


class DashboardSummaryResponse(BaseModel):
    data: DashboardSummaryData
    message: str


class ReportDateRange(BaseModel):
    date_from: date | None
    date_to: date | None


class ProgramReportEventSummary(BaseModel):
    event_id: int
    event_title: str
    event_date: date
    event_status: Literal["draft", "open", "closed", "archived"]
    total_attendance: int
    valid_attendance: int


class ProgramSummaryData(BaseModel):
    program_id: int
    program_name: str
    program_status: Literal["active", "archived"]
    date_range: ReportDateRange
    total_events: int
    total_attendance: int
    events_by_status: EventStatusCounts
    attendance_by_status: AttendanceStatusCounts
    events: list[ProgramReportEventSummary]


class ProgramSummaryResponse(BaseModel):
    data: ProgramSummaryData
    message: str


class SexCounts(BaseModel):
    female: int
    male: int
    unspecified: int


class DocumentationConsentCounts(BaseModel):
    accepted: int
    declined: int


class EventAttendanceReportData(BaseModel):
    event_id: int
    event_title: str
    event_date: date
    venue: str
    event_status: Literal["draft", "open", "closed", "archived"]
    program_id: int
    program_name: str
    total_attendance: int
    attendance_by_status: AttendanceStatusCounts
    attendees_by_sex: SexCounts
    documentation_consent: DocumentationConsentCounts


class EventAttendanceReportResponse(BaseModel):
    data: EventAttendanceReportData
    message: str
