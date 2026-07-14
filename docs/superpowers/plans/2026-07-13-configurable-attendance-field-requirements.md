# Configurable Attendance Field Requirements Implementation Plan

**Goal:** Add normalized per-event required/optional policies for the existing
fixed attendance fields without introducing a form builder.

**Architecture:** Store system-owned field definitions separately from each
event's requirement snapshot. Keep request parsing permissive only for
configurable fields, then enforce the selected event's policy in the service
layer. Use the existing event-access rules, audit builder, fixed public form,
and fixed DICT PDF layout.

**Tech stack:** Python, FastAPI, Pydantic v2, SQLAlchemy 2, MySQL 8, Pytest,
ReportLab, Mermaid, and Draw.io.

**Execution rules:** Use test-driven development. Run the focused RED test
before each production change, then focused and full GREEN tests. Work inline
in the current workspace. The user owns Git, so do not commit or run Git
operations.

---

## Task 1: Normalized Schema And ORM Models

**Files:**

- Create: `backend/app/models/attendance_fields.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/programs.py`
- Modify: `backend/app/models/attendance.py`
- Modify: `backend/tests/test_models.py`
- Modify: `others/database/schema.sql`
- Modify: `others/database/seed-core.sql`
- Create: `others/database/migrations/2026-07-13-add-attendance-field-settings.sql`
- Modify: `others/database/smoke-test.sql`
- Modify: `others/database/data-dictionary.md`
- Modify: `others/database/README.md`

### Step 1: Write failing metadata tests

Add tests that require:

- `attendance_form_fields` and `event_attendance_field_settings` in metadata.
- The expected composite primary key and foreign keys.
- Unique `display_order` and Boolean checks where consistent with current SQL.
- Event relationships to field settings.
- Nullable `affiliation`, `designation_category`, and `sex` columns.
- Existing locked attendance columns remain non-null.

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_models.py -q
```

Expected: RED because the new tables and nullability do not exist.

### Step 2: Implement ORM models

Add:

- `AttendanceFormField`
- `EventAttendanceFieldSetting`
- composite key `(event_id, field_key)`
- relationships from `Event` and `AttendanceFormField`
- nullable ORM types for the three configurable attendance columns

Keep fixed field keys as explicit backend constants so typos cannot silently
create unsupported form behavior.

### Step 3: Update fresh-install and one-time migration SQL

The migration script must:

1. Create both normalized tables.
2. Insert all approved field definitions and defaults.
3. Backfill one settings row per existing event and field.
4. Make the three configurable attendance columns nullable.
5. Preserve existing attendance values.

The fresh `schema.sql` and `seed-core.sql` must produce the same final schema
and default rows. Update smoke SQL to verify field counts, default values,
backfilled event snapshots, and nullable attendance columns.

### Step 4: Run focused verification

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_models.py tests/test_orm_smoke_check.py -q
.\.venv\Scripts\python.exe -m compileall -q app
```

Expected: GREEN without changing unrelated models.

---

## Task 2: Default Settings During Event Creation

**Files:**

- Modify: `backend/app/services/event_service.py`
- Modify: `backend/tests/test_event_routes.py`
- Modify: `backend/scripts/orm_smoke_check.py`

### Step 1: Write failing event-creation tests

Require a new event to receive a complete snapshot containing:

- Four locked required fields.
- Four configurable fields required by default.
- Six configurable fields optional by default.

Require event creation and setting creation to commit atomically. Simulate a
settings failure and verify rollback/no partial event.

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_event_routes.py -q
```

Expected: RED because event creation does not create settings.

### Step 2: Implement snapshot creation

During `create_event`:

1. Load active system field definitions.
2. Verify the complete supported field set exists.
3. Attach one setting row per definition using `default_is_required`.
4. Commit the event and settings in one transaction.

Do not read global defaults during later submissions; submissions must use the
event snapshot.

### Step 3: Extend ORM smoke output

Report the new table counts and verify that the smoke event has the complete
settings snapshot.

### Step 4: Run focused verification

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_event_routes.py tests/test_models.py tests/test_orm_smoke_check.py -q
```

Expected: GREEN.

---

## Task 3: Admin Read And Update API

**Files:**

- Create: `backend/app/schemas/attendance_field_settings.py`
- Create: `backend/app/services/attendance_field_settings_service.py`
- Create: `backend/app/api/attendance_field_settings.py`
- Modify: `backend/app/api/router.py`
- Create: `backend/tests/test_attendance_field_setting_routes.py`
- Modify: `backend/tests/test_audit_service.py` only if a reusable assertion is needed

### Step 1: Write failing route tests

Cover:

- `GET /api/events/{event_id}/attendance-field-settings`
- `PATCH /api/events/{event_id}/attendance-field-settings`
- Super Admin access.
- Assigned Program Admin access.
- Rejected unassigned Program Admin access.
- Complete ordered response with labels, values, and configurable flags.
- Partial updates for configurable keys.
- Rejected unknown and locked keys.
- Rejected updates for closed and archived events.
- Allowed updates for draft and open events.
- No audit row for repeated values.
- One atomic audit row for an actual multi-field change.
- Rollback when either settings or audit persistence fails.

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_attendance_field_setting_routes.py -q
```

Expected: RED with missing routes.

### Step 2: Implement schemas and service boundaries

The service must own:

- event lookup and role/assignment scope
- event-status edit lock
- supported/configurable key validation
- address-policy dependency validation
- old/new value comparison
- atomic settings and audit persistence

Use the existing audit builder. Record action
`updated_attendance_field_requirements`, entity type `event`, and the event ID.

### Step 3: Implement API routes

Return the standard success/error envelope. Keep field order stable using
`display_order`. Map validation conflicts to field-specific errors without
exposing internal SQL details.

### Step 4: Run focused regression tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_attendance_field_setting_routes.py tests/test_event_routes.py tests/test_audit_service.py -q
```

Expected: GREEN.

---

## Task 4: Public Metadata And Dynamic Submission Validation

**Files:**

- Modify: `backend/app/schemas/public_attendance.py`
- Modify: `backend/app/api/public_attendance.py`
- Modify: `backend/app/services/public_attendance_service.py`
- Modify: `backend/tests/test_public_attendance_routes.py`

### Step 1: Write failing public-event metadata tests

Require `GET /api/public/events/{event_code}` to return the complete Boolean
field-requirement map for the event. It must not expose admin-only metadata or
database IDs for settings rows.

### Step 2: Write failing dynamic validation tests

Cover at minimum:

- Optional affiliation, designation, and sex may be omitted and stored as null.
- Each field is rejected when its event setting requires it.
- Documentation consent distinguishes omitted from explicit `false` during
  validation; explicit decline is valid when a response is required.
- Optional omitted documentation consent stores `false`.
- Required signature accepts typed text or an image and rejects both omitted.
- Optional signature accepts both omitted.
- Required PSGC group uses conditional province behavior.
- Optional PSGC group accepts no address but rejects a partial hierarchy.
- Required street/postal policies work only with required PSGC policy.
- An open-event setting change affects the next submission but not existing
  stored rows.
- Locked field validation and duplicate-email behavior remain unchanged.

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_public_attendance_routes.py -q
```

Expected: RED because parsing and service validation still enforce one static
policy.

### Step 3: Make configurable fields parse as optional

Keep format and length validation in Pydantic, but allow absence for fields
whose required state depends on the event. Use `None` to distinguish an omitted
documentation-consent response from explicit `false`.

Do not weaken locked field parsing or required database consent.

### Step 4: Implement event-policy validation

Load the event with its setting snapshot, convert settings into a validated
map, then apply field and dependency rules before duplicate-sensitive writes.
Store optional values consistently and keep signature file cleanup behavior on
all rollback paths.

### Step 5: Run focused regression tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_public_attendance_routes.py tests/test_signature_service.py tests/test_public_reference_routes.py -q
```

Expected: GREEN.

---

## Task 5: Nullable Record Responses And Fixed PDF Compatibility

**Files:**

- Modify: `backend/app/schemas/attendance_records.py`
- Modify: `backend/app/api/attendance_records.py` if response mapping needs normalization
- Modify: `backend/app/services/attendance_sheet_service.py`
- Modify: `backend/app/services/attendance_sheet_pdf.py`
- Modify: `backend/tests/test_attendance_record_routes.py`
- Modify: `backend/tests/test_attendance_sheet_service.py`
- Modify: `backend/tests/test_attendance_sheet_pdf.py`

### Step 1: Write failing nullable-record tests

Require admin record list/detail endpoints to return `null` safely for omitted
optional affiliation, designation, and sex values.

### Step 2: Write failing PDF tests

Require:

- Fixed DICT columns remain unchanged.
- Missing optional affiliation/designation produces blank cells.
- Missing sex produces no F/M mark.
- Missing signature produces a blank signature cell.
- Mixed old/new records paginate without renderer errors.

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_attendance_record_routes.py tests/test_attendance_sheet_service.py tests/test_attendance_sheet_pdf.py -q
```

Expected: RED where current schemas or renderer types assume non-null values.

### Step 3: Implement nullable response and renderer support

Update annotations and mapping only where approved fields may be null. Keep
locked identity/email behavior and valid-attendee export selection unchanged.

### Step 4: Run focused regression tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_attendance_record_routes.py tests/test_attendance_sheet_service.py tests/test_attendance_sheet_pdf.py tests/test_attendance_sheet_export_routes.py -q
```

Expected: GREEN.

---

## Task 6: Current Documentation And Diagram Updates

**Files:**

- Modify: `backend/README.md`
- Modify: `others/mvp-requirements-v1.md`
- Modify: `others/system-process-flow.md`
- Modify: `others/user-roles-and-permission-matrix.md`
- Modify: `others/backend/backend-api-plan.md`
- Modify: relevant DFD text/source files under `others/dfd/`
- Modify: `others/erd/normalized-mysql-erd.md`
- Modify: `others/erd/README.md`
- Modify: `others/erd/source/attendance-system-erd.mmd`
- Modify: `others/erd/source/render_erd_drawio.py` if the new tables need layout support
- Regenerate: ERD SVG, PNG, and Draw.io artifacts
- Regenerate: affected DFD SVG, PNG, and Draw.io artifacts only when their source changes

### Step 1: Update authoritative documents

Document:

- fixed fields with per-event required/optional policy
- locked fields and reasons
- approved defaults
- draft/open editing and future-only behavior
- address dependencies
- normalized tables
- fixed PDF behavior
- explicit non-goal: no form builder

Remove any stale wording that says every configurable field is always required.

### Step 2: Update ERD and relevant DFD sources

Show both normalized tables and their relationships. Keep field settings inside
the system boundary; they are not an external entity or imported template.

### Step 3: Regenerate and validate artifacts

Run the repository render scripts. Parse generated SVG and Draw.io files as XML
and visually inspect only affected diagrams for clipping, unreadable labels, or
incorrect relationships.

---

## Task 7: Migration Handoff And Final Verification

**Files:**

- Modify: this plan's checkboxes while executing
- Modify: `others/database/README.md` with the exact PowerShell-to-MySQL CLI command

### Step 1: Run all automated checks that do not need the migrated live DB

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app scripts
.\.venv\Scripts\python.exe -m pip check
```

### Step 2: Validate OpenAPI contracts

Assert through `app.openapi()` that:

- Admin settings GET/PATCH routes exist and require Bearer authentication.
- Public event details expose the requirement map.
- Multipart attendance submission still exposes fixed form fields directly.
- No form-builder CRUD route exists.

### Step 3: User applies the one-time migration

The user runs the documented migration through MySQL CLI. Do not apply it on
their behalf unless they explicitly ask.

### Step 4: Run live database verification after migration

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.orm_smoke_check
```

Also run `others/database/smoke-test.sql` through the user's preferred MySQL CLI
pipeline and verify the new table/default/backfill checks.

### Step 5: Final scoped review

Confirm:

- No custom-field or form-builder behavior was added.
- Locked requirements cannot be bypassed.
- Existing records remain valid.
- Setting and audit writes are atomic.
- PDF columns remain fixed.
- Docs, schema, ERD, and affected DFD artifacts agree.
- No Git operation was performed.
