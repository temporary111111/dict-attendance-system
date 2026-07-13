# Auth Foundation Design

## Goal

Build the first backend authentication layer for admin users using JWT access
tokens only. This covers login, current-user lookup, logout response, password
hashing, and reusable role guards.

## Scope

Included:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- Password hashing and password verification
- JWT access token creation and verification
- Current user dependency
- Role helpers for `super_admin` and `program_admin`

Not included yet:

- Refresh tokens
- Password reset
- Email verification
- Frontend login page
- User management endpoints
- Database-stored tokens or sessions

## Auth Flow

1. Admin submits email and password.
2. Backend checks `users.password_hash`.
3. Backend checks `account_status = 'active'`.
4. Backend checks role is `super_admin` or `program_admin`.
5. Backend returns a JWT access token.
6. Frontend sends the token as `Authorization: Bearer <token>`.
7. Backend verifies the token signature, reads `user_id`, then loads the user
   from MySQL.

## Token Storage Decision

The JWT access token is not stored in the database. Frontend keeps the token,
and backend verifies it using `JWT_SECRET_KEY`.

Kapag kailangan na later ng force logout or token revocation before expiry,
magdadagdag tayo ng DB-backed session/token table. Hindi muna siya part ng MVP
auth foundation.

## Security Rules

- Failed login must return the same generic message for wrong email or password.
- Inactive users cannot log in.
- External attendees cannot log in because they are not stored as `users`.
- Protected endpoints must check the current user from the token and database.
- Role-specific endpoints must enforce backend checks, not just frontend button
  hiding.
