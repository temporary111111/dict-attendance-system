# Program Management Batch Design

## Goal

Complete the Program and Program Admin Assignment APIs as one backend batch.
Programs represent real DICT initiatives such as Free Wi-Fi for All, eGov
Super App, and National Broadband Plan.

## Access Rules

- Super Admin can list and view every program.
- Program Admin can list and view only programs with an active assignment.
- Only Super Admin can create, edit, archive, or restore programs.
- Only Super Admin can list, create, reactivate, or revoke assignments.
- Program Admin assignments apply to a program, not to individual events.

## Program Contract

Endpoints:

- `GET /api/programs`
- `POST /api/programs`
- `GET /api/programs/{programId}`
- `PATCH /api/programs/{programId}`
- `PATCH /api/programs/{programId}/archive`

Program creation requires an active owning organizational unit. Program names
are unique case-insensitively inside the same owning unit. Updates are partial;
`description: null` clears the description. The archive endpoint accepts
`program_status` as `active` or `archived`, allowing controlled restoration.
Restoration requires an active owning unit.

## Assignment Contract

Endpoints:

- `GET /api/programs/{programId}/admins`
- `POST /api/programs/{programId}/admins`
- `PATCH /api/program-admin-assignments/{assignmentId}/revoke`

Only active users with an active `program_admin` role can be assigned. New
assignments require an active program. An already-active pair returns a
conflict. Because `(program_id, user_id)` is unique, assigning a revoked pair
reactivates the existing row, clears `revoked_at`, and records the new assigner
and assignment time. Revocation is idempotent and retains the row for history.

## Architecture

- `schemas/programs.py` owns request and response contracts for the batch.
- `services/program_service.py` owns visibility, program validation, and writes.
- `services/program_assignment_service.py` owns assignment lifecycle rules.
- Separate route modules keep program routes and assignment routes focused.
- SQLAlchemy uniqueness constraints remain the final race-condition protection.

## Errors

Standard errors include `PROGRAM_NOT_FOUND`, `FORBIDDEN`,
`PROGRAM_NAME_ALREADY_EXISTS`, `PROGRAM_ARCHIVED`,
`ASSIGNMENT_ALREADY_ACTIVE`, `ASSIGNMENT_NOT_FOUND`, and field-level
`VALIDATION_ERROR` responses.

## Testing

Route tests cover both roles, visibility, validation, duplicate handling,
partial updates, archive/restore, assignment creation/reactivation/revocation,
and authentication. The full backend suite runs after focused tests.
