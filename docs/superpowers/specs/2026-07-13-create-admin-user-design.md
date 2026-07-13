# Create Admin User Design

## Goal

Payagan ang authenticated Super Admin na gumawa ng `super_admin` o
`program_admin` account sa `POST /api/users`.

## Request

Required fields:

- `full_name`: trimmed, 1 to 150 characters
- `email`: valid email, maximum 150 characters
- `password`: 8 to 72 characters and no more than 72 UTF-8 bytes
- `role_id`: positive ID of an active admin role

Optional field:

- `org_unit_id`: positive ID of an active organizational unit, or `null`

The backend normalizes `full_name` and stores email in lowercase. The new
account starts with `account_status = "active"`.

## Business Rules

- Only an active Super Admin can use the endpoint.
- Email must be unique, case-insensitively.
- Role must exist, be active, and be `super_admin` or `program_admin`.
- Organizational unit must exist and be active when supplied.
- Plain passwords are never stored or returned.
- Duplicate email returns `409 EMAIL_ALREADY_EXISTS`.
- Invalid role or organizational unit returns `422 VALIDATION_ERROR` with a
  field-specific message.

## Architecture

`app/api/users.py` owns the HTTP route and maps service errors to API errors.
`app/services/user_service.py` owns validation against current database data,
password hashing, and the transaction. `app/schemas/users.py` owns request and
response validation.

FastAPI request validation errors will use the existing standard error shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Some fields are invalid.",
    "fields": {}
  }
}
```

## Success Response

The endpoint returns `201` and the new user without `password` or
`password_hash`. The response includes compact nested role and organizational
unit data for immediate frontend display.

