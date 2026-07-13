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
```

These endpoints return active records for admin account creation and require a
Super Admin Bearer token.

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
