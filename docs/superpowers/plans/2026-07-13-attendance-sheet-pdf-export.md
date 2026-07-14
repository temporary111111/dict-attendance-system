# Attendance Sheet PDF Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:executing-plans and superpowers:test-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Add a protected event-level endpoint that generates one DICT-format
PDF containing every valid attendee of the selected event and atomically logs
the export.

**Architecture:** A database-independent ReportLab renderer accepts simple
event/row data and returns PDF bytes. A service performs role checks, loads one
event and its valid attendance records, safely resolves private signatures,
calls the renderer, and commits one export row plus one audit row. A small
FastAPI route returns the bytes as a private attachment.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, MySQL 8, ReportLab 4,
Pillow, Pypdf 6, Pytest.

## Global Constraints

- The admin selects one event; the PDF contains all `valid` attendees of that
  event only.
- Export is allowed for `draft`, `open`, `closed`, and `archived` events.
- Super Admin can export any event. Program Admin requires an active assignment
  to the event's program.
- Generate PDF bytes in memory. Do not retain a PDF file; persist
  `file_path = NULL`.
- Add no MySQL migration and make no ERD structural change.
- Use the provided PDF only as a layout reference; it is not a runtime import.
- New code comments and docstrings must be concise, beginner-readable Taglish.
- Do not run Git commands or create commits. The user owns version control.

---

### Task 1: Core DICT PDF Renderer

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/assets/dict-logo.png`
- Create: `backend/app/services/attendance_sheet_pdf.py`
- Create: `backend/tests/test_attendance_sheet_pdf.py`

**Interfaces:**
- Produces: `AttendanceSheetEvent`, `AttendanceSheetRow`,
  `AttendanceSheetPDFError`, and
  `render_attendance_sheet_pdf(event, rows, *, logo_path) -> bytes`.
- The renderer receives already-authorized, already-resolved data and has no
  FastAPI, database, or settings dependency.

- [x] **Step 1: Add and install bounded PDF dependencies**

Add:

```text
reportlab>=4.4.10,<5.0
pypdf>=6.14,<7.0
```

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Expected: ReportLab 4.x and Pypdf 6.x install successfully under Python 3.11.

- [x] **Step 2: Extract and verify the DICT logo asset**

Extract image xref `15` from page 1 of
`others/[ Attendance ] Coding Competition - Coding Competition.pdf` into
`backend/app/assets/dict-logo.png`. This is a generated binary asset, not a
runtime dependency on the source PDF.

Verify with Pillow:

```python
from pathlib import Path
from PIL import Image

path = Path("app/assets/dict-logo.png")
with Image.open(path) as image:
    image.verify()
assert path.stat().st_size > 0
```

- [x] **Step 3: Write failing renderer contract tests**

Create tests that define the desired data contract and inspect output with
Pypdf:

```python
from datetime import date
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.services.attendance_sheet_pdf import (
    AttendanceSheetEvent,
    AttendanceSheetRow,
    render_attendance_sheet_pdf,
)


def make_event():
    return AttendanceSheetEvent(
        office_name="DICT Regional Office No. V - Bicol",
        event_title="Digital Inclusion Orientation",
        venue="DICT Regional Office",
        event_date=date(2026, 8, 15),
    )


def make_row(number=1):
    return AttendanceSheetRow(
        row_number=number,
        attendee_name="Maria Santos Reyes",
        affiliation="Municipality of San Fernando",
        designation_category="Government Official",
        sex="F",
        email="maria.reyes@example.com",
        consent_documentation_publication=False,
        consent_database_processing=True,
        signature_text="Maria Santos Reyes",
        signature_image_path=None,
    )


def test_renderer_generates_landscape_pdf_with_event_and_attendee_text():
    pdf = render_attendance_sheet_pdf(
        make_event(),
        [make_row()],
        logo_path=Path("app/assets/dict-logo.png"),
    )

    reader = PdfReader(BytesIO(pdf))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert pdf.startswith(b"%PDF-")
    assert len(reader.pages) == 1
    assert float(reader.pages[0].mediabox.width) > float(
        reader.pages[0].mediabox.height
    )
    assert "Digital Inclusion Orientation" in text
    assert "Maria Santos Reyes" in text
    assert "Municipality of San Fernando" in text


def test_renderer_generates_one_page_for_zero_valid_records():
    pdf = render_attendance_sheet_pdf(
        make_event(),
        [],
        logo_path=Path("app/assets/dict-logo.png"),
    )
    assert len(PdfReader(BytesIO(pdf)).pages) == 1
```

- [x] **Step 4: Run renderer tests and verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_attendance_sheet_pdf.py -q
```

Expected: collection fails because `attendance_sheet_pdf` does not exist.

- [x] **Step 5: Implement the minimal one-page renderer**

Define frozen dataclasses with these exact fields:

```python
@dataclass(frozen=True)
class AttendanceSheetEvent:
    office_name: str
    event_title: str
    venue: str
    event_date: date


@dataclass(frozen=True)
class AttendanceSheetRow:
    row_number: int
    attendee_name: str
    affiliation: str
    designation_category: str
    sex: Literal["F", "M"]
    email: str
    consent_documentation_publication: bool
    consent_database_processing: bool
    signature_text: str | None
    signature_image_path: Path | None
```

Implement `render_attendance_sheet_pdf` using `SimpleDocTemplate` with
`landscape(A4)`, the extracted logo, centralized `PRIVACY_NOTICE`, and a
ReportLab `Table`. Use `AFFILIATION` rather than `SCHOOL/UNIVERSITY`, keep the
two consent columns, mark F/M and consent values, and escape attendee-provided
text before placing it in `Paragraph` objects. Catch ReportLab/Pillow I/O errors
and raise `AttendanceSheetPDFError`.

- [x] **Step 6: Run renderer tests until GREEN**

Run the focused file and confirm both tests pass.

---

### Task 2: Pagination, Wrapping, And Signatures

**Files:**
- Modify: `backend/app/services/attendance_sheet_pdf.py`
- Modify: `backend/tests/test_attendance_sheet_pdf.py`

**Interfaces:**
- Keeps the Task 1 renderer signature unchanged.
- Adds no filesystem authorization; paths passed to the renderer are already
  safe absolute `Path` objects or `None`.

- [x] **Step 1: Write failing pagination and signature tests**

Add these helpers before the tests:

```python
def render(rows):
    return render_attendance_sheet_pdf(
        make_event(), rows, logo_path=Path("app/assets/dict-logo.png")
    )


def extract_text(pdf_bytes):
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
```

Then add tests for:

```python
def test_renderer_paginates_27_standard_rows_without_blank_pages():
    rows = [make_row(number=index) for index in range(1, 28)]
    reader = PdfReader(
        BytesIO(
            render_attendance_sheet_pdf(
                make_event(), rows, logo_path=Path("app/assets/dict-logo.png")
            )
        )
    )
    assert len(reader.pages) == 2
    assert "Digital Inclusion Orientation" in (reader.pages[1].extract_text() or "")


def test_renderer_wraps_long_values_without_losing_text():
    row = replace(
        make_row(),
        affiliation="A very long government agency and local office name",
    )
    text = extract_text(render([row]))
    assert "A very long government agency" in text
    assert "local office name" in text


def test_renderer_embeds_valid_png_signature(tmp_path):
    signature = tmp_path / "signature.png"
    Image.new("RGBA", (240, 80), "white").save(signature)
    pdf = render([replace(make_row(), signature_image_path=signature)])
    assert pdf.startswith(b"%PDF-")


def test_renderer_uses_typed_signature_when_image_is_missing(tmp_path):
    row = replace(
        make_row(),
        signature_image_path=tmp_path / "missing.png",
        signature_text="Typed Signature Fallback",
    )
    assert "Typed Signature Fallback" in extract_text(render([row]))
```

Also assert the repeated table heading and privacy notice appear on every page.

- [x] **Step 2: Run new tests and verify RED**

Expected failures: one-page-only output, no image embedding, or missing
repeated header behavior.

- [x] **Step 3: Implement dynamic pages and signature cells**

- Repeat the logo/event/privacy block through the document page callback.
- Repeat grouped table headings with `repeatRows`.
- Limit each normal chunk to at most 26 rows while allowing ReportLab to move a
  wrapped row safely to the next page.
- Use `reportlab.platypus.Image` for an existing PNG, preserving aspect ratio.
- Fall back to escaped typed signature when the image is absent or unreadable.
- Keep a complete header and empty table when `rows` is empty.
- Do not add a `PageBreak` after the final chunk.

- [x] **Step 4: Run renderer and existing signature tests until GREEN**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_attendance_sheet_pdf.py tests/test_signature_service.py -q
```

---

### Task 3: Role-Aware Export Service And Atomic History

**Files:**
- Create: `backend/app/services/attendance_sheet_service.py`
- Create: `backend/tests/test_attendance_sheet_service.py`

**Interfaces:**
- Produces this result type:

```python
@dataclass
class AttendanceSheetExportResult:
    pdf_bytes: bytes
    filename: str
    export: AttendanceSheetExport
```

- Produces `generate_attendance_sheet_export(db, event_id, current_user, *,
  logo_path, signature_directory, ip_address, user_agent) ->
  AttendanceSheetExportResult`.

- Produces exceptions: `AttendanceSheetEventNotFoundError`,
  `AttendanceSheetAccessDeniedError`, `AttendanceSheetGenerationError`, and
  `AttendanceSheetExportPersistenceError`.

- [x] **Step 1: Write failing service tests**

Use a focused fake session that records `scalar`, `scalars`, `add`, `flush`,
`commit`, and `rollback`. Cover:

- Super Admin across all four event statuses.
- Active Program Admin assignment success.
- Missing/revoked assignment denial.
- Event not found.
- SQL text contains `attendance_status = valid` and ascending submitted/ID
  ordering.
- Composed name and owning organizational unit mapping.
- Safe signature resolution and typed fallback.
- Export fields: PDF, null path, selected event, acting user, valid count.
- Audit fields and request metadata.
- One flush and one commit for export plus audit.
- Renderer failure adds no export/audit rows.
- Flush/commit failure calls rollback and raises the persistence exception.

The central success assertion is:

```python
result = generate_attendance_sheet_export(
    session,
    5,
    make_user("super_admin"),
    logo_path=Path("app/assets/dict-logo.png"),
    signature_directory=tmp_path / "signatures",
    ip_address="127.0.0.1",
    user_agent="pytest",
)

assert result.pdf_bytes.startswith(b"%PDF-")
assert result.export.event_id == 5
assert result.export.export_format == "pdf"
assert result.export.file_path is None
assert result.export.total_records == 2
assert session.committed is True
assert session.added_objects[-1].action == "generated_attendance_sheet"
assert session.added_objects[-1].entity_type == "attendance_sheet_export"
```

- [x] **Step 2: Run service tests and verify RED**

Expected: import failure because `attendance_sheet_service` is absent.

- [x] **Step 3: Implement event access and valid-record mapping**

Load the event with:

```python
select(Event).options(
    selectinload(Event.program).selectinload(Program.owning_unit)
).where(Event.event_id == event_id)
```

For Program Admin, query an active `ProgramAdminAssignment`. Load records with:

```python
select(AttendanceRecord).where(
    AttendanceRecord.event_id == event_id,
    AttendanceRecord.attendance_status == "valid",
).order_by(
    AttendanceRecord.submitted_at.asc(),
    AttendanceRecord.attendance_id.asc(),
)
```

Create sequential `AttendanceSheetRow` values and resolve each image through
`resolve_signature_image(signature_directory, stored_path)`.

- [x] **Step 4: Implement render-first, atomic persistence**

Call the renderer before adding database rows. Then:

```python
export = AttendanceSheetExport(
    event_id=event.event_id,
    exported_by_user_id=current_user.user_id,
    export_format="pdf",
    file_path=None,
    total_records=len(records),
)
db.add(export)
db.flush()
db.add(build_audit_log(
    user_id=current_user.user_id,
    action="generated_attendance_sheet",
    entity_type="attendance_sheet_export",
    entity_id=export.export_id,
    description=(
        f"Generated PDF attendance sheet for event {event.event_id} "
        f"with {len(records)} valid records."
    ),
    old_values=None,
    new_values={
        "event_id": event.event_id,
        "export_format": "pdf",
        "total_records": len(records),
        "event_status": event.event_status,
    },
    ip_address=ip_address,
    user_agent=user_agent,
))
db.commit()
```

Rollback and raise `AttendanceSheetExportPersistenceError` on any persistence
exception. Sanitize the event code to ASCII letters, numbers, dot, underscore,
and hyphen for the attachment filename; fall back to `event-{event_id}`.

- [x] **Step 5: Run service tests until GREEN**

Run the new service tests plus attendance-record and audit service regressions.

---

### Task 4: Protected PDF Export Route

**Files:**
- Create: `backend/app/api/attendance_sheet_exports.py`
- Modify: `backend/app/api/router.py`
- Create: `backend/tests/test_attendance_sheet_export_routes.py`

**Interfaces:**
- Adds `POST /api/events/{event_id}/attendance-sheet-exports`.
- Returns raw `application/pdf` bytes through `StreamingResponse`.

- [x] **Step 1: Write failing route tests**

Cover authentication, status-independent success, assigned/unassigned Program
Admin behavior, event not found, generation failure, persistence failure, and
headers:

```python
response = client.post("/api/events/5/attendance-sheet-exports")

assert response.status_code == 200
assert response.headers["content-type"] == "application/pdf"
assert response.headers["cache-control"] == "private, no-store"
assert "attachment" in response.headers["content-disposition"]
assert response.content.startswith(b"%PDF-")
```

Assert error codes `EVENT_NOT_FOUND`, `FORBIDDEN`,
`ATTENDANCE_SHEET_GENERATION_FAILED`, and
`ATTENDANCE_SHEET_EXPORT_FAILED`.

- [x] **Step 2: Run route tests and verify RED**

Expected: `404` because the router is not registered.

- [x] **Step 3: Implement and register the route**

The route extracts client IP and user agent, resolves the fixed backend logo
path, calls `generate_attendance_sheet_export`, maps domain errors, and returns:

```python
return StreamingResponse(
    BytesIO(result.pdf_bytes),
    media_type="application/pdf",
    headers={
        "Content-Disposition": f'attachment; filename="{result.filename}"',
        "Cache-Control": "private, no-store",
    },
)
```

Declare the OpenAPI success response as PDF and keep authentication through
`get_current_user`.

- [x] **Step 4: Run route and attendance regression tests until GREEN**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_attendance_sheet_export_routes.py tests/test_attendance_sheet_service.py tests/test_attendance_sheet_pdf.py tests/test_attendance_record_routes.py tests/test_public_attendance_routes.py -q
```

---

### Task 5: Current Documentation, DFD, And Final Verification

**Files:**
- Modify: `backend/README.md`
- Modify: `others/backend/backend-api-plan.md`
- Modify: `others/mvp-requirements-v1.md`
- Modify: `others/system-process-flow.md`
- Modify: `others/user-roles-and-permission-matrix.md`
- Modify: `others/dfd/level-0/dfd-level-0-text.md`
- Modify: `others/dfd/level-1/dfd-level-1-text.md`
- Modify: `others/dfd/level-2/dfd-level-2-text.md`
- Modify: `others/dfd/source/dfd-level-0.mmd`
- Modify: `others/dfd/source/dfd-level-1.mmd`
- Modify: `others/dfd/source/dfd-level-2.mmd`
- Modify: `others/dfd/source/render_mermaid_style_drawio.py`
- Regenerate: current DFD PNG, SVG, and Draw.io artifacts
- Modify: this plan's checkboxes

**Interfaces:**
- Documents the implemented route and removes the remaining conditional wording
  around assigned Program Admin attendance-sheet export.

- [x] **Step 1: Update current documentation**

Document:

- One selected event per export.
- All valid attendees of that event are included.
- All event statuses are exportable.
- Super Admin global and active Program Admin assigned-scope permission.
- In-memory private PDF, null file path, export history, and audit history.
- General `AFFILIATION` output heading.
- PDF only for MVP.

Remove the current open question about whether Program Admin can download an
official sheet. Keep unrelated retention and future-format questions open.

- [x] **Step 2: Update and regenerate DFD artifacts**

Remove `if allowed` / `if permitted` from Program Admin sheet flows. Keep the
existing P7 attendance-sheet generation process and D6/D7 connections; no new
entity or store is needed. Run:

```powershell
python others/dfd/source/render_mermaid_style_drawio.py
python others/dfd/source/render_mermaid_diagrams.py
```

Visually inspect Level 0, Level 1, and Level 2 updated PNGs.

- [x] **Step 3: Generate and inspect representative PDFs**

Use the renderer test factories to produce:

- One page with one typed signature.
- One page with one image signature.
- Multiple pages with 27 standard records.
- One page with zero records.

Inspect page count and extracted text with Pypdf, then render representative
pages with the temporary PDF inspection tooling for visual checks: no overlap,
no clipped text, readable signatures, repeated headers, and no blank tail page.

- [x] **Step 4: Run final verification**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app scripts
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m scripts.orm_smoke_check
```

Also assert through `app.openapi()` that the POST route exists, requires Bearer
authentication, and advertises `application/pdf`. Scan current authoritative
docs for stale conditional Program Admin download wording. Validate generated
SVG/Draw.io XML and verify no schema or ERD source timestamp changed.

- [x] **Step 5: Review the complete scoped work**

Confirm the implementation contains no PDF storage directory, no schema/ERD
change, no unrelated refactor, no exposed signature path, and no Git operation.
