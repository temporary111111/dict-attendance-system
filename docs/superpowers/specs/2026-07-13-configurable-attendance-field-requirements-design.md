# Configurable Attendance Field Requirements Design

**Date:** 2026-07-13

## Goal

Allow an authorized admin to choose which existing attendance fields are
required or optional for each event. The attendance form remains fixed: admins
cannot add, remove, rename, reorder, or hide fields.

## Core Rules

- Field requirements are configured per event.
- Every fixed field remains visible on the public form.
- Locked identity and consent fields remain required for system integrity.
- Configurable fields use safe defaults when an event is created.
- Settings may be edited while an event is `draft` or `open`.
- A change made while an event is open affects future submissions only.
- Existing attendance records are never invalidated by a later setting change.
- Settings cannot be edited when an event is `closed` or `archived`.
- Actual setting changes are recorded in the audit log.

## Field Defaults

### Required And Locked

| Field key | Reason |
| --- | --- |
| `first_name` | Minimum attendee identity |
| `last_name` | Minimum attendee identity |
| `email` | Event-level duplicate detection |
| `consent_database_processing` | Current approved rule for storing attendee data |

### Required By Default, Admin-Configurable

- `affiliation`
- `designation_category`
- `sex`
- `consent_documentation_publication`

For documentation/publication consent, required means the attendee must answer.
A `false` response is still a valid answer and means the attendee declined.

### Optional By Default, Admin-Configurable

- `middle_name`
- `suffix`
- `signature`
- `psgc_address`
- `street_address`
- `postal_code`

`signature` represents the existing typed-signature or uploaded-image choices.
When required, either choice satisfies the rule. When optional, either may be
provided or both may be omitted.

## Data Model

### `attendance_form_fields`

System-owned definitions for the fixed fields:

- `field_key` primary key
- `field_label`
- `default_is_required`
- `is_admin_configurable`
- `display_order`

There is no admin CRUD API for this table. Adding a new fixed field remains a
controlled system change that includes database, backend, and frontend work.

### `event_attendance_field_settings`

Requirement snapshot for each event and fixed field:

- `event_id` foreign key to `events`
- `field_key` foreign key to `attendance_form_fields`
- `is_required`
- `created_at`
- `updated_at`
- composite primary key: `event_id`, `field_key`

When an event is created, the service copies every system field default into
this table. Existing events are backfilled with the same defaults during the
migration. This snapshot prevents a future global default change from silently
changing existing events.

The design remains normalized: field metadata is stored once, while each event
stores only its selected requirement value.

### Attendance Record Nullability

The following existing columns become nullable because their fields may be
optional:

- `attendance_records.affiliation`
- `attendance_records.designation_category`
- `attendance_records.sex`

Existing nullable name, signature, and address columns remain nullable.
`consent_documentation_publication` remains non-null and stores `false` when an
optional response is omitted. Locked fields keep their existing non-null rules.

## Admin API

### Read Settings

`GET /api/events/{event_id}/attendance-field-settings`

Returns the complete fixed field list with labels, current requirement values,
and whether each field is admin-configurable.

### Update Settings

`PATCH /api/events/{event_id}/attendance-field-settings`

Accepts a partial map of configurable field keys to Boolean requirement values.
Unknown keys and attempts to modify locked fields are rejected. Repeating the
current value is allowed but does not create an audit log.

Permissions follow event ownership:

- Super Admin may manage any accessible non-closed, non-archived event.
- Program Admin needs an active assignment to the event's program.

An actual change writes the settings and one audit log in the same transaction.
The audit entry contains the old and new requirement values.

## Public Event And Submission Flow

The public event-details response includes the complete field-requirement map.
The frontend uses it only to display `Required` or `Optional` states; it does not
dynamically create or remove controls.

Configurable request fields become optional at schema parsing time so that the
service can validate them against the selected event. The service then:

1. Loads the open event and its field settings.
2. Applies locked requirements.
3. Applies the event's configurable requirements.
4. Validates field formats, signature choice, and PSGC hierarchy.
5. Stores nullable optional values consistently.

Validation errors continue to use the standard `VALIDATION_ERROR` response with
field-specific messages. Missing required signatures continue to use
`SIGNATURE_REQUIRED`.

## Address Dependencies

`psgc_address` controls the PSGC hierarchy as a group:

- Required: region, city/municipality, and barangay are required.
- Province is required only when the selected city/municipality belongs to one.
- Optional: no address is accepted, but a partially supplied hierarchy is not.

An admin cannot require `street_address` or `postal_code` while leaving
`psgc_address` optional. The update endpoint rejects that conflicting policy.

## Form And PDF Behavior

- All fixed controls remain visible on the public form.
- Required fields show a required marker.
- Optional fields show an `Optional` label.
- Locked controls appear required in admin settings with a disabled toggle and
  a short reason.
- The official PDF keeps the fixed DICT columns.
- Missing optional values produce blank PDF cells.
- The signature column remains available for later wet signatures.
- Attendance-sheet export still includes all valid attendees for one event.

## Error Handling

- Unauthorized event scope: existing access-denied response.
- Closed or archived event update: conflict response.
- Unknown field key: validation error.
- Locked field update: field-not-configurable validation error.
- Conflicting address requirements: validation error.
- Database failure: roll back both setting changes and audit entry.

## Testing

Automated coverage will include:

- Default setting creation and existing-event backfill.
- Super Admin and assigned Program Admin access.
- Rejection of unassigned Program Admin access.
- Rejection of locked, unknown, closed-event, and archived-event changes.
- No-op update behavior and atomic audit logging.
- Dynamic validation for every configurable field group.
- Required-response semantics for documentation consent.
- Typed/image/omitted signature combinations.
- PSGC group and street/postal dependency rules.
- Future-only effect of settings changed on an open event.
- Public event requirement metadata.
- Blank optional values in stored records and generated PDFs.
- OpenAPI contracts and full regression coverage.

## Documentation Impact

Implementation updates the MySQL schema, SQLAlchemy models, seed/smoke data,
ERD source and generated artifacts, current requirements and process documents,
and relevant DFD text where field-requirement configuration is described. It
does not introduce a form builder or a new external entity.

## Out Of Scope

- Adding custom attendance fields.
- Renaming, hiding, deleting, or reordering fixed fields.
- Different input types or validation expressions configured by admins.
- Retroactively invalidating or editing existing attendance records.
- Removing fixed columns from the official attendance-sheet PDF.
