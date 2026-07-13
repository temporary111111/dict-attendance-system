# Admin User Detail Design

## Goal

Bigyan ang Super Admin ng `GET /api/users/{userId}` para makita ang isang
specific admin account.

## Rules

- Active Super Admin JWT is required.
- `userId` must be a positive integer.
- The response uses the same safe user fields as `GET /api/users`.
- Role and optional organizational unit are eager-loaded.
- Password and password hash are never returned.
- A missing user returns `404 USER_NOT_FOUND`.

## Implementation

The existing users API module will query `users` directly by primary key with
the same relationship loading and safe formatter used by the list endpoint.
No separate service is needed for this read-only lookup.

