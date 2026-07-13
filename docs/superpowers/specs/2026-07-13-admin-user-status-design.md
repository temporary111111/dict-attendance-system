# Admin User Status Design

## Goal

Payagan ang Super Admin na i-activate o i-deactivate ang admin account gamit ang
`PATCH /api/users/{userId}/status`.

## Request

```json
{
  "account_status": "inactive"
}
```

Only `active` and `inactive` are accepted. Repeating the current status is a
valid idempotent request.

## Rules

- Active Super Admin JWT is required.
- Target user must exist.
- A Super Admin cannot deactivate their own current account.
- Reactivation requires the user's assigned role to remain active and be an
  admin role.
- Deactivation does not delete the user or historical relationships.
- Status changes do not edit profile fields or passwords.

## Responses

- `200`: safe user data with the resulting status
- `404 USER_NOT_FOUND`: target user does not exist
- `409 CANNOT_DEACTIVATE_OWN_ACCOUNT`: actor targets their own account
- `422 VALIDATION_ERROR`: invalid status or inactive/non-admin role on reactivation

## Implementation

The endpoint passes both target ID and authenticated Super Admin ID to the user
service. The service enforces transition rules, commits the status, and returns
the same safe user result used by other account endpoints.

