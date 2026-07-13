# Update Admin User Design

## Goal

Payagan ang Super Admin na i-update ang profile at organizational assignment ng
admin account gamit ang `PATCH /api/users/{userId}`.

## Editable Fields

- `full_name`
- `email`
- `role_id`
- `org_unit_id`

All fields are optional because this is a partial update, but at least one field
must be supplied. Explicit `org_unit_id: null` removes the organizational unit.
The endpoint does not edit passwords or `account_status`; those use separate
workflows.

## Rules

- Active Super Admin JWT is required.
- The target user must exist.
- Email remains unique case-insensitively and is stored lowercase.
- A supplied role must be an active admin role.
- A supplied non-null unit must exist and be active.
- Existing account status is preserved.
- Password fields are never accepted or returned.

## Responses

- `200`: updated safe user data
- `404 USER_NOT_FOUND`: target user does not exist
- `409 EMAIL_ALREADY_EXISTS`: another user has the email
- `422 VALIDATION_ERROR`: empty payload or invalid field/reference

## Implementation

The existing user service will centralize role, unit, and email checks so create
and update follow the same rules. The users route maps domain errors into the
existing standard API response shape.

