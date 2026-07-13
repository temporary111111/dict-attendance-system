# List Admin Users Design

## Goal

Bigyan ang Super Admin ng `GET /api/users` para makita ang lahat ng admin
accounts na kailangan niyang i-manage.

## Rules

- Active Super Admin JWT is required.
- Both active and inactive accounts are included.
- Results are ordered by full name, then user ID.
- Each item includes safe account fields, compact role data, and optional
  organizational unit data.
- Password and password hash are never returned.
- No pagination, search, or filters in this first list slice.

## Implementation

The existing users route will run one SQLAlchemy query with eager loading for
role and organizational unit relationships. Reusing one response formatter
keeps `POST /api/users` and `GET /api/users` consistent.

