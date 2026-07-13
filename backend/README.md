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
POST /api/events/{eventId}/attendance-link
POST /api/events/{eventId}/open
POST /api/events/{eventId}/close
PATCH /api/events/{eventId}/archive
```

Super Admins manage events under any active program. Program Admins can manage
events only under programs where they have an active assignment. Generate the
attendance link and QR before opening collection. Open events must be closed
before their event or parent program can be archived.

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

The submission endpoint accepts `multipart/form-data` with `first_name`,
optional `middle_name`, `last_name`, optional `suffix`, `affiliation`,
`designation_category`, `sex`, `email`, both consent fields, and either
`signature_text` or a PNG/JPEG `signature_image`.

Address fields are optional. Once any address field is provided,
`region_code`, `city_municipality_code`, and `barangay_code` are required.
`province_code` stays optional for PSGC areas that are not province-based;
`street_address` and `postal_code` are optional. Submitted codes must form an
active hierarchy in the local PSGC tables.

The event must be open. A normalized email can be submitted only once per
event. Uploaded signatures are verified, re-encoded as PNG, and saved under
the private directory configured below. The backend does not expose this
directory as static media.

```text
SIGNATURE_DIRECTORY=storage/signatures
SIGNATURE_MAX_BYTES=5242880
```

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
