# Create Organizational Unit Design

## Goal

Payagan ang Super Admin na gumawa ng DICT organizational unit gamit ang
`POST /api/organizational-units`.

## Request Fields

- `unit_name`: required, trimmed, 1 to 200 characters
- `unit_type`: required, trimmed and lowercase, 1 to 50 characters
- `unit_code`: optional, trimmed and uppercase, 1 to 50 characters
- `parent_unit_id`: optional positive integer; `null` creates a root unit

New units start with `is_active = true`.

## Rules

- Active Super Admin JWT is required.
- Supplied unit code must be unique case-insensitively.
- Supplied parent must exist and be active.
- Unit type remains flexible text because the complete DICT hierarchy labels
  are not hardcoded in the database.
- Creation never modifies an existing parent.

## Responses

- `201`: created organizational unit
- `409 UNIT_CODE_ALREADY_EXISTS`: duplicate supplied unit code
- `422 VALIDATION_ERROR`: invalid fields or parent

## Implementation

A focused organizational-unit service validates the parent and unit code,
creates the active row, and handles database uniqueness races. The existing
organizational-unit route and response shape are reused.

