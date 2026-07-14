# Attendance Sheet PDF Export Design

## Goal

Generate a downloadable attendance-sheet PDF from current event data using the
fixed DICT layout supplied by the supervisor. The export must remain flexible
for admins, enforce program-level access, include only valid attendance
records, and create traceable export and audit rows.

## Approved Decisions

- PDF generation is allowed for `draft`, `open`, `closed`, and `archived`
  events. Event status does not block an authorized admin.
- Super Admin can export any event.
- Program Admin can export only events under programs where the user has an
  active assignment.
- Each request generates a fresh snapshot from current database values.
- Generated PDF bytes are returned directly and are not retained on the
  server. `attendance_sheet_exports.file_path` remains `NULL`.
- The admin selects one event. The PDF includes all records from that selected
  event whose `attendance_status = valid`; it does not combine multiple events.
- A zero-record event still produces a valid one-page attendance sheet.
- PDF is the only format in this batch. XLSX and CSV remain future work.
- The provided PDF is a visual/layout reference, not a file imported or
  modified at runtime.

## Source Template Findings

The supplied file is a landscape A4 PDF with 39 pages. Its useful attendance
layout contains:

- DICT logo and government heading.
- Owning DICT office, event title, venue, and event date.
- Privacy notice from the supervisor-provided format.
- Attendance table with row number, name, affiliation, designation/category,
  F/M sex markers, email, two consent markers, and signature.
- Sixty numbered rows spread across the first three useful pages.

The remaining source pages are accidental blank print-range pages. The system
must not reproduce them. Output pages are created dynamically from the number
and height of actual records.

## API Contract

### Generate And Download

`POST /api/events/{event_id}/attendance-sheet-exports`

The request has no body because this batch supports one approved output:
the fixed DICT PDF.

Successful response:

- Status: `200 OK`
- Content type: `application/pdf`
- `Content-Disposition: attachment` with a sanitized filename based on the
  event code, for example `attendance-sheet-SMOKE-TEST-ORIENTATION.pdf`.
- `Cache-Control: private, no-store`

The endpoint returns raw PDF bytes, not the normal JSON success envelope.

### Errors

- `401`: missing, expired, or invalid admin access token.
- `403 FORBIDDEN`: Program Admin has no active assignment to the event's
  program.
- `404 EVENT_NOT_FOUND`: event does not exist.
- `500 ATTENDANCE_SHEET_GENERATION_FAILED`: PDF generation failed.
- `500 ATTENDANCE_SHEET_EXPORT_FAILED`: export or audit persistence failed.

Errors continue to use the project's standard JSON error envelope.

## PDF Data Mapping

### Event Header

- Office heading: `event.program.owning_unit.unit_name`.
- Event title: `event.event_title`.
- Venue: `event.venue`.
- Date: `event.event_date`, formatted as a readable date such as
  `August 15, 2026`.
- Logo: a project asset extracted from the supervisor-provided PDF and stored
  with the backend. The source PDF is not needed at runtime.

### Attendance Rows

- Row number: one-based sequence across the complete export.
- Name: first, middle, last, and suffix joined without extra spaces.
- Affiliation: `attendance_records.affiliation`. The heading uses
  `AFFILIATION` so government offices, companies, LGUs, and other
  non-school attendees are represented correctly.
- Designation/category: `designation_category`.
- Sex: mark either F or M.
- Email: `email`.
- Consent columns: visually mark each stored boolean independently.
- Signature:
  - Safely resolved image signature takes priority.
  - If no usable image exists, render `signature_text`.
  - A missing legacy signature does not abort the complete export; its cell
    remains blank.

Address fields do not appear because the supplied official layout has no
address column.

## Layout Rules

- Landscape A4 page size.
- Full event header, privacy notice, and table heading repeat on every page so
  each printed page remains understandable on its own.
- The layout targets up to 26 standard-height records per page, matching the
  useful first page of the supplied format.
- Long names, affiliations, designations, and email values wrap instead of
  overflowing or being silently discarded. Wrapped rows may reduce the number
  of records on that page.
- Signature images preserve aspect ratio and fit inside the signature cell.
- Output contains no trailing blank pages.
- A zero-record export contains the complete header and an empty attendance
  table on one page.
- The privacy notice text from the supplied template is centralized in one
  module constant so DICT can update it later without changing layout logic.

## Query And Ordering

The export service loads the event together with its program and owning
organizational unit. It then retrieves all valid attendance records for that
event, ordered by:

1. `submitted_at ASC`
2. `attendance_id ASC`

This produces stable chronological row numbering. Invalid, duplicate, and void
records do not contribute to the PDF or `total_records`.

## Export And Audit Transaction

The service first renders the complete PDF in memory. No database history is
written when rendering fails.

After successful rendering, one transaction creates:

1. `attendance_sheet_exports`
   - `event_id`: selected event.
   - `exported_by_user_id`: acting admin.
   - `export_format`: `pdf`.
   - `file_path`: `NULL`.
   - `total_records`: number of valid records included.
2. `audit_logs`
   - `action`: `generated_attendance_sheet`.
   - `entity_type`: `attendance_sheet_export`.
   - `entity_id`: newly flushed export ID.
   - `new_values_json`: event ID, format, total records, and event status at
     generation time.
   - Request IP address and user agent when available.

The export row is flushed to obtain its ID before creating the audit row. The
transaction commits only after both rows are ready. A persistence failure rolls
back both rows and returns no PDF response.

Each successful request creates a new export and audit row, even when the
underlying event data has not changed. This records each generated snapshot.

## Architecture

- `app/services/attendance_sheet_service.py`
  - Enforces event access.
  - Loads valid records and signature paths.
  - Calls the PDF renderer.
  - Persists export and audit rows atomically.
- `app/services/attendance_sheet_pdf.py`
  - Contains the privacy text, PDF data structures, and ReportLab rendering.
  - Has no database or FastAPI dependency.
- `app/api/attendance_sheet_exports.py`
  - Maps service errors and returns a private streaming PDF response.
- `app/api/router.py`
  - Registers the export router.
- `app/assets/dict-logo.png`
  - Contains the DICT logo extracted from the supplied supervisor template.
- `app/core/config.py`
  - No export-directory setting is required because generated files are not
    retained.

ReportLab is used for deterministic landscape table layout and embedded
signature images. Pypdf is used by automated tests to inspect generated page
count and text without depending on a desktop PDF reader.

## Schema Impact

The existing `attendance_sheet_exports` and `audit_logs` tables already support
the design. No MySQL migration or ERD change is required.

## Security And Privacy

- The endpoint always requires authenticated admin access.
- Program Admin authorization is checked by active assignment in the backend.
- Signature files are resolved only inside `SIGNATURE_DIRECTORY` using the
  existing safe resolver.
- Raw signature paths never appear in the API response or generated PDF
  metadata.
- The PDF response is marked private and non-cacheable.
- The server does not retain generated PDFs, reducing duplicate storage of
  personal data.

## Testing

Test-first coverage includes:

- Super Admin export for every event status.
- Assigned Program Admin success and unassigned/revoked denial.
- Missing event response.
- Query includes only valid records and uses stable chronological ordering.
- Correct event, office, attendee, consent, and typed-signature text.
- Safely resolved image signature rendering and missing-image fallback.
- Multiple pages without trailing blank pages.
- Zero valid records still producing a one-page PDF.
- `application/pdf`, attachment filename, and private cache headers.
- Export row values, audit values, acting user, request metadata, and one
  atomic commit.
- PDF-render failure writes no export/audit rows.
- Database failure rolls back export and audit and returns no PDF.
- OpenAPI registration and regression coverage for existing routes.

Final verification runs the focused export tests, complete backend suite,
Python compilation, dependency validation, ORM smoke check, generated PDF text
inspection, and visual inspection of representative one-page and multi-page
samples.
