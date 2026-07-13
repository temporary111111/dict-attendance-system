# Attendance Record Management Batch Design

## Goal

Deliver authenticated attendance-record review for Super Admin and Program
Admin users, including paginated event records, complete record details,
protected signature images, controlled status updates, and transactional audit
logging. Keep the project documentation and DFD artifacts consistent with the
implemented behavior.

## Source Of Truth

The implementation follows this priority when older documents disagree:

1. Approved current project decisions.
2. The tested MySQL schema and SQLAlchemy models.
3. Passing tests and implemented API behavior.
4. Current MVP requirements, process flow, permission matrix, and API plan.
5. Current DFD and ERD sources.
6. Handoff, scratch, and completed implementation plans as historical context.

Historical questions about Google Forms, a form builder, signature capture,
PSGC collection, and JWT authentication are already resolved. They must not
override the current fixed public form, required signature choice, optional
PSGC address section, private signature storage, and JWT access-token design.

## Scope

The batch adds these authenticated endpoints:

- `GET /api/events/{eventId}/attendance-records`
- `GET /api/attendance-records/{attendanceId}`
- `GET /api/attendance-records/{attendanceId}/signature`
- `PATCH /api/attendance-records/{attendanceId}/status`

Manual correction of attendee fields, hard deletion, attendance-sheet export,
dashboard reporting, and full audit-log browsing are outside this batch.

## Access Rules

- Super Admin can list, view, retrieve signatures, and change status for any
  attendance record.
- Program Admin can perform the same actions only for events under programs
  where the user has an active `program_admin_assignments` row.
- A revoked assignment immediately removes attendance-record access.
- Authorized historical access remains available for closed or archived events.
- Neither role can freely edit submitted attendee identity, consent, address,
  email, or signature data in this batch.
- Full audit-trail browsing remains Super Admin only in a later audit module.

The backend performs every permission check. Frontend visibility is not an
authorization boundary.

## Event Attendance List

`GET /api/events/{eventId}/attendance-records` accepts:

- `page`: integer, default `1`, minimum `1`.
- `pageSize`: integer, default `25`, minimum `1`, maximum `100`.
- `status`: optional `valid`, `duplicate`, `invalid`, or `void`.
- `search`: optional trimmed text, maximum `100` characters.

Search matches attendee name fields, email, affiliation, and
designation/category. Results are ordered by `submitted_at DESC`, then
`attendance_id DESC` for stable pagination.

The standard success envelope contains:

```json
{
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "page_size": 25,
      "total_items": 0,
      "total_pages": 0
    }
  },
  "message": "Attendance records retrieved."
}
```

Each list item contains the attendance ID, composed attendee name, email,
affiliation, designation/category, sex, status, duplicate flag, and submission
timestamp. It does not expose consent details, address details, signature text,
or signature storage paths.

## Attendance Detail

`GET /api/attendance-records/{attendanceId}` returns:

- All submitted attendee fields.
- Both consent values.
- Attendance status, duplicate flag, and timestamps.
- Event ID, title, date, venue, and status.
- Program ID and name.
- Optional normalized address with PSGC codes and display names.
- Signature metadata containing `typed_name`, `has_image`, and a protected
  API URL when an image exists.

Inactive PSGC rows remain readable for historical attendance records. The API
never returns `signature_image_path` or an absolute filesystem path.

## Protected Signature Image

`GET /api/attendance-records/{attendanceId}/signature` repeats the same
record-level access check as the detail endpoint. It resolves the stored
relative path only inside the configured private `SIGNATURE_DIRECTORY` and
returns the normalized PNG with `Cache-Control: private, no-store`.

Typed-only records, missing files, invalid stored paths, and non-files return
`404 SIGNATURE_IMAGE_NOT_FOUND`. The private signature directory remains
unmounted from static media.

## Status Update And Audit

`PATCH /api/attendance-records/{attendanceId}/status` accepts:

```json
{
  "attendance_status": "void",
  "reason": "Submitted using the wrong attendee email."
}
```

`attendance_status` must be `valid`, `duplicate`, `invalid`, or `void`.
`reason` is required, trimmed, and between 3 and 300 characters. Any current
status may move to any allowed status because this is a controlled review
classification, not a workflow state machine.

An actual status change creates one `audit_logs` row in the same database
transaction as the attendance update:

- `action`: `attendance_status_changed`
- `entity_type`: `attendance_record`
- `entity_id`: attendance ID
- `user_id`: acting admin ID
- `old_values_json`: previous attendance status
- `new_values_json`: new attendance status and supplied reason
- `description`: concise human-readable status change and reason
- `ip_address` and `user_agent`: request metadata when available

If the requested status already matches the stored status, the endpoint is
idempotent: it returns the existing record without writing a duplicate audit
entry. A failed attendance or audit write rolls back both changes.

`duplicate_flag` remains a separate possible-duplicate review signal. The
status endpoint does not automatically set or clear it; `attendance_status`
is the official reviewed classification.

## Errors

- `401 NOT_AUTHENTICATED`, `TOKEN_EXPIRED`, or `INVALID_TOKEN`: no valid admin.
- `403 FORBIDDEN`: Program Admin is not actively assigned to the program.
- `404 EVENT_NOT_FOUND`: list target event does not exist.
- `404 ATTENDANCE_RECORD_NOT_FOUND`: detail/status target does not exist.
- `404 SIGNATURE_IMAGE_NOT_FOUND`: no safely retrievable image exists.
- `422 VALIDATION_ERROR`: invalid pagination, filter, status, search, or reason.

Responses use the project's existing standard error envelope.

## Architecture

- `schemas/attendance_records.py` defines list, pagination, detail, signature
  metadata, and status-update contracts.
- `services/attendance_record_service.py` owns queries, access checks,
  pagination, detail loading, and transactional status updates.
- `services/audit_service.py` builds audit rows without committing so the
  calling business transaction remains atomic and future modules can reuse it.
- `services/signature_service.py` gains a safe private-path resolver.
- `api/attendance_records.py` maps domain errors and serves the protected PNG.
- `api/router.py` registers the attendance-record router.

Existing tables and relationships are sufficient. This batch does not require
a MySQL schema migration or ERD structural change.

## Documentation And DFD Consistency

The batch updates current guidance to remove resolved ambiguity:

- Backend API plan: remove free attendee correction from this batch, allow
  assigned Program Admin status updates, and document pagination/signatures.
- Permission matrix: replace the Program Admin `Maybe` status permission with
  the approved assigned-program rule.
- MVP requirements and system process flow: record the same status and audit
  behavior.
- DFD Level 1 and Level 2 text/source/visuals: show authenticated attendance
  review, assignment validation, status updates, and D7 audit logging.
- Stack/database notes: resolve implemented JWT/signature-storage decisions and
  correct stale local database examples.
- Handoff and scratch files: clearly label them historical/non-authoritative
  instead of allowing old open questions to override current decisions.
- Add a documentation index that identifies authoritative current documents
  and historical implementation records.

The normalized ERD stays unchanged because the current attendance and audit
tables already support the design.

## Testing And Verification

Test-first route and service coverage includes:

- Pagination boundaries, stable ordering, status filters, and text search.
- Super Admin access and assigned/revoked Program Admin behavior.
- Closed and archived event historical access.
- Detail responses with and without normalized PSGC addresses.
- No private signature path in JSON.
- Protected image success, typed-only/missing file, path traversal, and access
  denial.
- Status updates for both admin roles, required reason, all allowed statuses,
  idempotency, and forbidden unassigned access.
- Correct audit content and transaction rollback when audit persistence fails.
- Authentication requirements and OpenAPI registration.

Final verification runs focused tests, the complete backend suite, Python
compilation, dependency validation, MySQL ORM smoke check, OpenAPI route audit,
documentation conflict scans, and regenerated DFD artifact checks.
