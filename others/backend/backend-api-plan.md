# Backend API Plan

## Program and Event Attendance Monitoring and Reporting System for DICT

This document describes the planned backend API behavior for the MVP. It is based on the current DFD, normalized MySQL ERD, permissions matrix, and tested MySQL schema.

## 1. Backend Assumptions

* The backend will expose REST-style API endpoints.
* The API will use JSON for normal request and response bodies.
* Admin authentication is required for Super Admin and Program Admin modules.
* External attendees do not log in. They submit attendance through a public event link or QR code.
* The public attendance page uses fixed input fields. The system will not include a Google Forms integration or a custom forms builder.
* The official attendance sheet is generated from saved event and attendance data using the fixed DICT-provided template format.
* Program Admin access must always be checked through `program_admin_assignments`.
* Official attendance sheet exports should include `attendance_records` with `attendance_status = 'valid'` by default.
* PSGC dropdown data should be read from local MySQL PSGC lookup tables, not from live PSA API calls during attendee submission.
* The selected backend stack is Python FastAPI with MySQL.
* The FastAPI backend will be API-only. It must not assume that frontend files are stored inside the backend project.
* The vanilla HTML, CSS, and JavaScript frontend may be hosted separately or deployed together with the backend later.
* CORS origins must be configurable because the frontend and backend may run on different hosts.

## 2. Standard Response Shape

Successful response:

```json
{
  "data": {},
  "message": "Request completed successfully."
}
```

Validation or business rule error:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Some fields are invalid.",
    "fields": {}
  }
}
```

Suggested common status codes:

| Status | Meaning |
| --- | --- |
| `200` | Successful read or update |
| `201` | Successful create |
| `400` | Invalid request format or business rule error |
| `401` | Not logged in |
| `403` | Logged in but not allowed |
| `404` | Record not found or not accessible |
| `409` | Duplicate or conflict, such as duplicate attendance email for the same event |
| `422` | Field validation failed |

## 3. Authentication API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `POST` | `/api/auth/login` | Public | Log in an admin user. | `users`, `roles` |
| `POST` | `/api/auth/logout` | Admin | End the current admin session. | Depends on auth implementation |
| `GET` | `/api/auth/me` | Admin | Return current logged-in admin user and role. | `users`, `roles`, `organizational_units` |

Login rules:

* Only active users can log in.
* Only Super Admin and Program Admin users can log in.
* Passwords must be checked against `users.password_hash`.
* Failed login must not reveal whether the email or password is wrong.

## 4. User and Role API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `GET` | `/api/users` | Super Admin | List admin users. | `users`, `roles`, `organizational_units` |
| `POST` | `/api/users` | Super Admin | Create an admin user. | `users`, `roles`, `organizational_units` |
| `GET` | `/api/users/{userId}` | Super Admin | View one admin user. | `users`, `roles`, `organizational_units` |
| `PATCH` | `/api/users/{userId}` | Super Admin | Update admin user profile fields. | `users` |
| `PATCH` | `/api/users/{userId}/status` | Super Admin | Activate or deactivate an admin user. | `users` |
| `GET` | `/api/roles` | Super Admin | List roles for admin user creation. | `roles` |

Important rules:

* `users.email` must be unique.
* Attendees are not created as `users`.
* Program Admins are actual DICT employees assigned to manage real DICT programs.

## 5. Organizational Unit API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `GET` | `/api/organizational-units` | Super Admin | List offices, divisions, sections, or units. | `organizational_units` |
| `POST` | `/api/organizational-units` | Super Admin | Create an organizational unit. | `organizational_units` |
| `PATCH` | `/api/organizational-units/{orgUnitId}` | Super Admin | Update an organizational unit. | `organizational_units` |

Important rules:

* Units can be hierarchical through `parent_org_unit_id`.
* A program uses `programs.owning_unit_id`.
* A user may use `users.org_unit_id`.

## 6. Program API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `GET` | `/api/programs` | Admin | List programs visible to the current admin. | `programs`, `organizational_units`, `program_admin_assignments` |
| `POST` | `/api/programs` | Super Admin | Create a program. | `programs` |
| `GET` | `/api/programs/{programId}` | Admin | View a visible program. | `programs`, `organizational_units` |
| `PATCH` | `/api/programs/{programId}` | Super Admin | Update program details. | `programs` |
| `PATCH` | `/api/programs/{programId}/archive` | Super Admin | Archive or deactivate a program. | `programs` |

Important rules:

* Programs are DICT initiatives or services, such as Free Wi-Fi for All, eGov Super App, and National Broadband Plan.
* Program Admins can view only assigned programs.
* Program Admins should not create or edit core program records in the MVP.
* Program names are unique inside the same owning organizational unit.
* Program archive and restore are status changes; the program row is not deleted.

## 7. Program Admin Assignment API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `GET` | `/api/programs/{programId}/admins` | Super Admin | List Program Admins assigned to a program. | `program_admin_assignments`, `users` |
| `POST` | `/api/programs/{programId}/admins` | Super Admin | Assign a Program Admin to a program. | `program_admin_assignments` |
| `PATCH` | `/api/program-admin-assignments/{assignmentId}/revoke` | Super Admin | Revoke a Program Admin assignment. | `program_admin_assignments` |

Important rules:

* `program_admin_assignments.program_id + user_id` must be unique.
* The assigned user must have the Program Admin role.
* Super Admin assigns Program Admins to programs, not to individual events.
* Assigning a previously revoked user-program pair reactivates the existing row.
* Revocation keeps the assignment row for history and records `revoked_at`.

## 8. Event API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `GET` | `/api/events` | Admin | List visible events. | `events`, `programs`, `program_admin_assignments` |
| `POST` | `/api/programs/{programId}/events` | Admin | Create an event under a program. | `events`, `program_admin_assignments` |
| `GET` | `/api/events/{eventId}` | Admin | View event details. | `events`, `programs` |
| `PATCH` | `/api/events/{eventId}` | Admin | Update allowed event fields. | `events`, `program_admin_assignments` |
| `GET` | `/api/events/{eventId}/attendance-field-settings` | Admin | View the event's fixed field requirements. | `attendance_form_fields`, `event_attendance_field_settings` |
| `PATCH` | `/api/events/{eventId}/attendance-field-settings` | Admin | Change configurable fields between required and optional. | `attendance_form_fields`, `event_attendance_field_settings`, `audit_logs` |
| `POST` | `/api/events/{eventId}/attendance-link` | Admin | Generate or refresh public attendance link and QR data. | `events` |
| `POST` | `/api/events/{eventId}/open` | Admin | Open attendance collection. | `events` |
| `POST` | `/api/events/{eventId}/close` | Admin | Close attendance collection. | `events` |
| `PATCH` | `/api/events/{eventId}/archive` | Super Admin | Archive an event. | `events` |

Important rules:

* Super Admin can create events under any program.
* Program Admin can create events only under assigned programs.
* Program Admin can edit events only under assigned programs.
* Each new event receives a snapshot of every fixed attendance field and its default requirement.
* Authorized admins may change configurable requirements only while the event is `draft` or `open`.
* First name, last name, email, and database-processing consent are locked as required.
* Admins cannot add, remove, rename, reorder, or hide fields; this is not a form builder.
* Actual requirement changes create one audit log entry. Existing attendance records are not revalidated.
* `events.event_code` must be unique.
* `events.public_attendance_url` is the public URL used by the QR code.
* Public attendance should accept submissions only when the event is open.
* Attendance-link refresh rotates the event code and replaces the QR PNG.
* Opening requires a generated attendance link and QR code.
* Closed events may be reopened; open and close actions are idempotent.
* Open events must be closed before the event or parent program is archived.
* Archived programs cannot accept event writes or be reopened.

Suggested event statuses:

| Status | Meaning |
| --- | --- |
| `draft` | Event exists but public attendance is not yet open. |
| `open` | Public attendance is currently accepting submissions. |
| `closed` | Attendance collection is finished. |
| `archived` | Event is hidden from normal active lists. |

## 9. Public Attendance API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `GET` | `/api/public/events/{eventCode}` | Public | Load public event details and its fixed field requirements. | `events`, `programs`, `event_attendance_field_settings` |
| `POST` | `/api/public/events/{eventCode}/attendance` | Public | Submit fixed attendance details. | `attendance_records`, `attendance_record_addresses`, PSGC tables |

Fixed attendance inputs:

| Input | Main Table Field |
| --- | --- |
| First name | `attendance_records.first_name` |
| Middle name (optional) | `attendance_records.middle_name` |
| Last name | `attendance_records.last_name` |
| Suffix (optional) | `attendance_records.suffix` |
| Sex | `attendance_records.sex` |
| Email | `attendance_records.email` |
| Affiliation | `attendance_records.affiliation` |
| Designation or category | `attendance_records.designation_category` |
| Documentation and publication consent | `attendance_records.consent_documentation_publication` |
| Database processing consent | `attendance_records.consent_database_processing` |
| Typed signature or PNG/JPEG image | `attendance_records.signature_text`, `attendance_records.signature_image_path` |

Optional address fields:

| Input | Table Field |
| --- | --- |
| Region | `attendance_record_addresses.region_code` |
| Province | `attendance_record_addresses.province_code` |
| City or municipality | `attendance_record_addresses.city_municipality_code` |
| Barangay | `attendance_record_addresses.barangay_code` |
| Street address | `attendance_record_addresses.street_address` |
| Postal code | `attendance_record_addresses.postal_code` |

Important rules:

* The public attendance page must be fixed, not dynamically built by admins.
* Submission uses `multipart/form-data` so text fields and an optional signature image can be sent together.
* The event must exist and must be open.
* `attendance_records.event_id + email` must be unique.
* If the same email submits again for the same event, the API should return `409 DUPLICATE_ATTENDANCE` and should not create another attendance row under the current schema.
* The whole address section is optional. If any address value is submitted, region, city or municipality, and barangay are required; province remains optional for non-province PSGC areas.
* Submitted PSGC codes must exist, be active, and form a matching hierarchy in the local PSGC tables.
* Database processing consent is locked as required and must be accepted.
* Affiliation, designation/category, sex, and the documentation/publication consent response are required by default but configurable per event.
* Middle name, suffix, signature, PSGC address, street address, and postal code are optional by default but configurable per event.
* When documentation/publication consent is required, the attendee must answer it; an explicit decline is still a valid response.
* When signature is required, either a typed signature or uploaded PNG/JPEG signature satisfies it.
* Uploaded signatures are verified, re-encoded as PNG, and stored in a private directory that is not exposed as static media.
* The confirmation message should not expose private admin data.

Suggested duplicate response:

```json
{
  "error": {
    "code": "DUPLICATE_ATTENDANCE",
    "message": "Attendance for this email has already been submitted for this event."
  }
}
```

## 10. Attendance Record API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `GET` | `/api/events/{eventId}/attendance-records` | Admin | Paginated list for an accessible event. | `attendance_records`, `events`, `program_admin_assignments` |
| `GET` | `/api/attendance-records/{attendanceId}` | Admin | View one attendance record. | `attendance_records`, `attendance_record_addresses`, PSGC tables |
| `GET` | `/api/attendance-records/{attendanceId}/signature` | Admin | Retrieve one authorized private signature PNG. | `attendance_records` |
| `PATCH` | `/api/attendance-records/{attendanceId}/status` | Admin | Mark record as valid, duplicate, invalid, or void with a reason. | `attendance_records`, `audit_logs` |

Important rules:

* Super Admin can view all attendance records.
* Program Admin can view and change status only for records from events under actively assigned programs.
* The event list supports `page`, `pageSize`, `status`, and `search`; page size is limited to 100.
* Status changes require a reason and create an audit row in the same transaction.
* Admins cannot freely edit attendee identity, consent, address, email, or signature fields in the MVP.
* Signature storage paths are private and never returned in JSON.
* MVP should avoid hard deleting attendance records. Use `attendance_status = 'void'` or `invalid` instead.

Status request:

```json
{
  "attendance_status": "void",
  "reason": "Submitted using the wrong attendee email."
}
```

## 11. Attendance Sheet Export API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `POST` | `/api/events/{eventId}/attendance-sheet-exports` | Admin | Generate and directly download the selected event's official PDF. | `events`, `programs`, `attendance_records`, `attendance_sheet_exports`, `audit_logs` |

Important rules:

* The generated file must follow the fixed DICT attendance sheet template format.
* The system does not import a template at runtime in the MVP. The layout should be implemented in the export generator.
* One request selects one event and includes all of that event's `attendance_status = 'valid'` records.
* `attendance_sheet_exports.total_records` stores the number of attendance rows included in the generated file.
* The MVP generates PDF only and returns it directly with private, non-cacheable headers.
* The server does not retain generated PDF files, so `attendance_sheet_exports.file_path` remains `NULL`.
* Generation is allowed for draft, open, closed, and archived events.
* Super Admin can export any event. Program Admin can export events only under actively assigned programs.
* The export row and audit row are saved in one database transaction.

## 12. Dashboard and Report API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `GET` | `/api/dashboard/summary` | Admin | Show dashboard summary counts visible to current admin. | `programs`, `events`, `attendance_records` |
| `GET` | `/api/reports/programs/{programId}/summary` | Admin | Show program-level event and attendance summary. | `programs`, `events`, `attendance_records` |
| `GET` | `/api/reports/events/{eventId}/attendance` | Admin | Show event attendance report data. | `events`, `attendance_records` |

Important rules:

* Super Admin reports can include all programs and events.
* Program Admin reports must be filtered to assigned programs only.
* Reports should clearly separate valid, duplicate, invalid, and void records.
* Dashboard operational totals include active programs and non-archived events only.
* Program summaries retain draft, open, closed, and archived event counts for historical reporting.
* Program summaries accept optional inclusive `dateFrom` and `dateTo` filters based on event date; `dateFrom` cannot be later than `dateTo`.
* Event attendance reports include status, sex, and documentation/publication consent breakdowns.
* Detailed attendee rows remain in the paginated attendance-record API; the official full attendee list remains the event attendance-sheet PDF.

## 13. PSGC Lookup API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `GET` | `/api/psgc/regions` | Public or Admin | List active regions. | `psgc_regions` |
| `GET` | `/api/psgc/provinces?regionCode={regionCode}` | Public or Admin | List active provinces for a region. | `psgc_provinces` |
| `GET` | `/api/psgc/cities-municipalities?regionCode={regionCode}&provinceCode={provinceCode}` | Public or Admin | List active cities or municipalities. | `psgc_cities_municipalities` |
| `GET` | `/api/psgc/barangays?cityMunicipalityCode={cityMunicipalityCode}` | Public or Admin | List active barangays. | `psgc_barangays` |

Important rules:

* Public attendance can use these endpoints for address dropdowns.
* The API should return only `is_active = 1` rows for normal dropdowns.
* Old inactive PSGC rows should not be deleted because old attendance records may still reference them.
* PSA API sync/import is an admin-side maintenance task, not a runtime dependency for attendee submission.

## 14. Audit Log API

| Method | Endpoint | Auth | Purpose | Tables |
| --- | --- | --- | --- | --- |
| `GET` | `/api/audit-logs` | Super Admin | List audit logs with filters. | `audit_logs`, `users` |

Supported filters:

* `page` and `pageSize` for newest-first pagination; page size is limited to 100.
* `userId`, `action`, `entityType`, and `entityId` for exact filtering.
* Inclusive `dateFrom` and `dateTo`; `dateFrom` cannot be later than `dateTo`.
* `search` across action, entity type, description, and actor name.

The response may include before/after JSON, IP address, and user agent because
the endpoint is restricted to Super Admin. The actor is nullable so historical
logs remain readable if the related user reference becomes null.

Actions that should be logged:

* Admin login success or failure, depending on security policy.
* User created, updated, activated, or deactivated.
* Program created or updated.
* Program Admin assigned or revoked.
* Event created, updated, opened, closed, or archived.
* Attendance record status changed.
* Attendance sheet generated or downloaded.

Audit fields:

| Field | Meaning |
| --- | --- |
| `actor_user_id` | Admin user who performed the action. |
| `action` | Machine-readable action key, such as `created_event`. |
| `entity_type` | Affected module or table, such as `event` or `attendance_record`. |
| `entity_id` | Primary key of the affected record, stored as a flexible value. |
| `description` | Human-readable explanation. |

## 15. Access Control Summary

| Rule | Required Backend Check |
| --- | --- |
| Super Admin can access all records. | Check role is `super_admin`. |
| Program Admin can access assigned programs only. | Check active row in `program_admin_assignments`. |
| Program Admin can create events only under assigned programs. | Check assignment before `INSERT INTO events`. |
| Program Admin can manage only assigned events. | Join `events` to `program_admin_assignments` through `program_id`. |
| External attendee can submit attendance only through public event route. | Validate `event_code` and event status. |
| Program Admin cannot bypass UI restrictions. | Backend must reject unauthorized direct API calls. |

## 16. Validation Rules

Admin-side validation:

* Required names, email, role, and account status for users.
* Unique email for users.
* Required program name and owning organizational unit for programs.
* Required event title, program, event date, event code, venue, and status for events.
* Unique event code.
* Valid role assignment when assigning a Program Admin.

Public attendance validation:

* Required name fields.
* Required valid email format.
* Required affiliation.
* Required designation or category.
* Required sex value matching allowed values.
* Required consent fields.
* Event must be open.
* Duplicate email for the same event must be rejected.
* PSGC codes must exist and be active when address fields are submitted.

## 17. Suggested Backend Build Order

1. Database connection and environment configuration.
2. Authentication and current-user middleware.
3. Role and assignment access guard helpers.
4. User, role, and organizational unit endpoints.
5. Program and Program Admin assignment endpoints.
6. Event endpoints and public attendance link generation.
7. Public event lookup and attendance submission endpoints.
8. Attendance record list and status endpoints.
9. Attendance sheet PDF generation and direct-download endpoint.
10. Dashboard and report endpoints.
11. PSGC lookup endpoints.
12. Audit log endpoints.

## 18. Open Technical Decisions

These decisions are not finalized by the current docs:

* Password reset process.
* Whether contact number should be added to `attendance_records`; it is not in the current tested schema.

Decisions already implemented:

* Admin authentication uses stateless JWT access tokens for the MVP.
* QR codes are generated locally using the Python `qrcode` package.
* Signature images use configurable private local storage.
* The first submission API accepts either typed or uploaded image signatures.
* Address fields are optional but are validated as one PSGC hierarchy when supplied.
* Attendance sheets use ReportLab PDF generation and Pypdf verification.
* Assigned Program Admins may generate attendance sheets for their program events.

## 19. MVP Non-Goals

These are intentionally outside the MVP backend plan:

* Google Forms integration.
* Dynamic form builder.
* Attendee login accounts.
* Live PSA API calls during public attendance submission.
* Hard deletion of attendance records.
* Automatic suspicious duplicate scoring beyond the current event plus email uniqueness rule.
