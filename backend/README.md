# DICT Attendance System Backend

FastAPI API-only backend for the DICT Program and Event Attendance Monitoring and Reporting System.

## Stack

* Python 3.11.x
* FastAPI
* Uvicorn
* SQLAlchemy 2.0
* PyMySQL
* MySQL 8.0+
* Pytest

## Setup

Run from this `backend` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `DATABASE_URL` to your local MySQL database:

```text
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/dict_attendance_system?charset=utf8mb4
JWT_SECRET_KEY=replace-with-a-long-random-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
```

## Run

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/health/db
```

## Auth

Admin authentication uses a JWT access token only for now. The token is not
stored in the database. The frontend stores the token and sends it through the
`Authorization` header:

```text
Authorization: Bearer <access_token>
```

Available auth endpoints:

```text
POST /api/auth/login
GET /api/auth/me
POST /api/auth/logout
```

`/api/auth/logout` is stateless in this MVP setup. It returns success, then the
frontend should remove the stored token.

Super Admin reference-data endpoints:

```text
GET /api/roles
GET /api/organizational-units
POST /api/organizational-units
PATCH /api/organizational-units/{orgUnitId}
```

The GET endpoints return active records for admin account creation.
`POST /api/organizational-units` accepts `unit_name`, `unit_type`, optional
`unit_code`, and optional `parent_unit_id`. The PATCH endpoint supports partial
field updates, soft activation/deactivation, and safe hierarchy changes. These
endpoints require a Super Admin Bearer token.

Create an admin account:

```text
GET /api/users
GET /api/users/{userId}
POST /api/users
PATCH /api/users/{userId}
PATCH /api/users/{userId}/status
```

`GET /api/users` lists active and inactive admin accounts, while
`GET /api/users/{userId}` returns one account. `POST /api/users` accepts
`full_name`, `email`, `password`, `role_id`, and optional `org_unit_id`. These
endpoints require a Super Admin token and never return the password or password
hash. `PATCH /api/users/{userId}` partially updates `full_name`, `email`,
`role_id`, or `org_unit_id`; it does not change passwords or account status.
`PATCH /api/users/{userId}/status` accepts `active` or `inactive`. A Super Admin
cannot deactivate their own current account.

Program management endpoints:

```text
GET /api/programs
POST /api/programs
GET /api/programs/{programId}
PATCH /api/programs/{programId}
PATCH /api/programs/{programId}/archive
GET /api/programs/{programId}/admins
POST /api/programs/{programId}/admins
PATCH /api/program-admin-assignments/{assignmentId}/revoke
```

Super Admins can manage every program and assignment. Program Admins can only
list or view programs where they have an active assignment. Programs use
`active` or `archived` status without deleting rows. Revoked assignments also
remain in the database; assigning the same Program Admin again reactivates the
existing unique assignment row.

Event management endpoints:

```text
GET /api/events
POST /api/programs/{programId}/events
GET /api/events/{eventId}
PATCH /api/events/{eventId}
GET /api/events/{eventId}/attendance-field-settings
PATCH /api/events/{eventId}/attendance-field-settings
POST /api/events/{eventId}/attendance-link
POST /api/events/{eventId}/open
POST /api/events/{eventId}/close
PATCH /api/events/{eventId}/archive
```

Super Admins manage events under any active program. Program Admins can manage
events only under programs where they have an active assignment. Generate the
attendance link and QR before opening collection. Open events must be closed
before their event or parent program can be archived.

Every new event receives its own snapshot of the fixed attendance fields.
Authorized admins can change only whether configurable fields are required or
optional while the event is `draft` or `open`. First name, last name, email,
and database-processing consent are always required. Field names, order, and
visibility cannot be changed, so this remains a fixed form rather than a form
builder.

QR generation uses these environment settings:

```text
PUBLIC_ATTENDANCE_URL_TEMPLATE=http://127.0.0.1:5500/attendance.html?event={event_code}
QR_CODE_DIRECTORY=storage/qr_codes
QR_CODE_URL_PREFIX=/media/qr-codes
```

`PUBLIC_ATTENDANCE_URL_TEMPLATE` must contain `{event_code}`. Refreshing an
attendance link rotates the code and replaces the locally stored QR PNG.

## Public Attendance

Attendees do not need an admin account. The fixed attendance page uses these
public endpoints:

```text
GET /api/public/events/{eventCode}
POST /api/public/events/{eventCode}/attendance
GET /api/psgc/regions
GET /api/psgc/provinces?regionCode={regionCode}
GET /api/psgc/cities-municipalities?regionCode={regionCode}&provinceCode={provinceCode}
GET /api/psgc/barangays?cityMunicipalityCode={cityMunicipalityCode}
```

The public event response includes `attendance_field_requirements`, which the
frontend uses to mark the fixed inputs required or optional. The submission
endpoint accepts `multipart/form-data` with the fixed name, affiliation,
designation/category, sex, email, consent, address, and optional signature
image input. The backend enforces the selected event's requirement
snapshot; existing submissions are not revalidated after a setting changes.

Address fields are optional by default. Once any address field is provided,
`region_code`, `city_municipality_code`, and `barangay_code` are required.
`province_code` stays optional for PSGC areas that are not province-based;
`street_address` and `postal_code` are optional. Submitted codes must form an
active hierarchy in the local PSGC tables. If an admin requires the PSGC
address group, region, city/municipality, and barangay become required while
province remains conditional. Requiring street address or postal code also
requires the PSGC address group.

The event must be open. A normalized email can be submitted only once per
event. Uploaded signatures are verified, re-encoded as PNG, and saved under
the private directory configured below. The backend does not expose this
directory as static media.

```text
SIGNATURE_DIRECTORY=storage/signatures
SIGNATURE_MAX_BYTES=5242880
```

## PSGC Masterlist Import

Super Admins can import an official PSA Excel masterlist through the admin UI.
The UI calls these protected endpoints:

```text
POST /api/admin/psgc/imports/preview
POST /api/admin/psgc/imports/apply
```

Both endpoints require `multipart/form-data` with `file` (`.xlsx`) and
`source_version`. Preview only validates headers, numeric codes, duplicates,
and the complete PSGC parent hierarchy. Apply validates the same file again,
then upserts all rows in one transaction and creates one audit log. The default
maximum upload size is 10 MiB and can be changed with `PSGC_IMPORT_MAX_BYTES`.

## Attendance Record Management

Authenticated admins can review event attendance through:

```text
GET /api/events/{eventId}/attendance-records
GET /api/attendance-records/{attendanceId}
GET /api/attendance-records/{attendanceId}/signature
PATCH /api/attendance-records/{attendanceId}/status
```

The event list supports `page`, `pageSize`, optional `status`, and optional
`search`. Super Admins can access all records. Program Admins can access and
change status only for events under actively assigned programs.

Status changes accept `valid`, `duplicate`, `invalid`, or `void` plus a
required reason. The status and audit row are saved in one transaction. Admins
cannot freely edit submitted attendee fields or hard delete attendance rows.
Signature images remain private and are served only by the authenticated
signature endpoint.

## Attendance Sheet PDF Export

Authenticated admins can generate one PDF for one selected event:

```text
POST /api/events/{eventId}/attendance-sheet-exports
```

The PDF contains all `valid` attendees of that event, ordered by submission
time. It follows the fixed DICT layout with the event header, privacy notice,
affiliation, designation/category, sex, email, consent, and signature columns.
Generation is allowed for every event status. Super Admins can export any
event, while Program Admins need an active assignment to the event's program.

Each request returns a private, non-cacheable PDF attachment. The server does
not retain the generated file: `attendance_sheet_exports.file_path` remains
`NULL`, while the export summary and audit log are saved in one transaction.

## Dashboard And Reports

Authenticated admins can retrieve role-scoped operational summaries through:

```text
GET /api/dashboard/summary
GET /api/reports/programs/{programId}/summary
GET /api/reports/events/{eventId}/attendance
```

The dashboard counts active programs, non-archived events, attendance status
totals, and five recent visible events. Super Admins see all matching data;
Program Admins see only programs with an active assignment.

Program summaries include all event statuses for the selected accessible
program and support optional inclusive `dateFrom` and `dateTo` event-date
filters. Event reports include attendance-status, sex, and documentation
consent breakdowns. Detailed attendee rows remain available through the
paginated attendance-record endpoint, while the official attendee list is
generated through the attendance-sheet PDF endpoint.

## Audit Logs

Only Super Admins can browse audit history:

```text
GET /api/audit-logs
```

The endpoint is ordered newest first and supports `page`, `pageSize`,
`userId`, `action`, `entityType`, `entityId`, inclusive `dateFrom`/`dateTo`,
and `search`. Search checks the action, entity type, description, and actor
name. Results include the affected entity, before/after JSON, request metadata,
and a nullable actor for historical rows whose user no longer exists.

## Create Local Super Admin

After running `others/database/schema.sql` and `others/database/seed-core.sql`,
create or update a local Super Admin from the `backend` folder:

```powershell
.\.venv\Scripts\Activate.ps1
python -m scripts.create_admin_user --email admin@example.test --full-name "System Super Admin"
```

The script asks for the password using a hidden terminal prompt. The plain
password is not stored in SQL files or printed in the terminal.

## Test

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -v
```

## ORM Smoke Check

After importing `others/database/schema.sql` and setting `DATABASE_URL` in `.env`,
run this from the `backend` folder to verify that the SQLAlchemy models can query
your actual MySQL database:

```powershell
.\.venv\Scripts\Activate.ps1
python -m scripts.orm_smoke_check
```

## Frontend Hosting

The frontend is separate from this FastAPI backend. The frontend should call the backend using a configurable API base URL such as:

```text
http://127.0.0.1:8000/api
```

When the frontend runs on a different host or port, add that frontend origin to `CORS_ORIGINS` in `.env`.
