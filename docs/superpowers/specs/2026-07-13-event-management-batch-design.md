# Event Management Batch Design

## Goal

Complete event management, public attendance link/QR generation, and event
status lifecycle as one backend batch.

## Access Rules

- Super Admin can list, view, create, and edit events under any active program.
- Program Admin can list, view, create, and edit only under programs with an
  active assignment.
- Only Super Admin can archive events.
- Archived events are excluded from the normal event list but remain available
  by ID to authorized admins for historical viewing.

## Event Contract

Endpoints:

- `GET /api/events`
- `POST /api/programs/{programId}/events`
- `GET /api/events/{eventId}`
- `PATCH /api/events/{eventId}`
- `POST /api/events/{eventId}/attendance-link`
- `POST /api/events/{eventId}/open`
- `POST /api/events/{eventId}/close`
- `PATCH /api/events/{eventId}/archive`

Creation accepts title, optional description, venue, and date. The backend
generates an unguessable unique event code and starts the event in `draft`.
Updates are partial, cannot move an event to another program, and reject
archived events.

## Attendance Link and QR

The backend uses the `qrcode` package with Pillow to generate a PNG locally.
The attendance page URL is built from the configurable
`PUBLIC_ATTENDANCE_URL_TEMPLATE`, which must contain `{event_code}`. Generated
files are stored under configurable `QR_CODE_DIRECTORY` and served through
`/media/qr-codes`.

Every attendance-link refresh rotates the event code, creates a new URL and QR
PNG, commits their paths with the event, and removes the superseded PNG after a
successful write. No external QR service receives attendance URLs.

## Status Lifecycle

- `draft -> open`: requires a generated attendance URL and QR.
- `open -> closed`: records `closed_at`.
- `closed -> open`: allowed for controlled reopening; clears `closed_at`.
- Repeating `open` or `close` on the same state is idempotent.
- A draft event cannot be closed directly.
- An open event must be closed before Super Admin can archive it.
- Archived events cannot be edited, opened, closed, or refreshed.

## Architecture

- `schemas/events.py` defines event request and response contracts.
- `services/event_service.py` owns visibility, access, writes, and transitions.
- `services/qr_code_service.py` owns QR filesystem generation and cleanup.
- `api/events.py` maps domain errors to standard API responses.
- Existing `events` columns and constraints require no database migration.

## Testing

Route tests cover both roles, visibility, event writes, unique code generation,
access denial, QR refresh, transitions, archive rules, and authentication. QR
tests verify that a real PNG is written and served through its HTTP path. Focused tests,
the full backend suite, MySQL ORM smoke check, and OpenAPI route audit complete
the quality gate.
