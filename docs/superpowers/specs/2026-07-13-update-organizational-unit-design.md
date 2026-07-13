# Update Organizational Unit Design

## Goal

Payagan ang Super Admin na baguhin ang existing DICT organizational unit gamit
ang `PATCH /api/organizational-units/{orgUnitId}` nang hindi nasisira ang
organizational hierarchy.

## Request Fields

Lahat ng fields ay optional, pero kailangang may kahit isang field:

- `unit_name`: trimmed, 1 to 200 characters
- `unit_type`: trimmed and lowercase, 1 to 50 characters
- `unit_code`: trimmed and uppercase; `null` removes the code
- `parent_unit_id`: positive integer; `null` makes the unit a root
- `is_active`: boolean

## Rules

- Active Super Admin JWT is required.
- Target unit must exist.
- Supplied unit code must be unique case-insensitively, excluding the target.
- Supplied parent must exist and be active.
- A unit cannot be its own parent or a child of one of its descendants.
- An inactive unit cannot be used as the parent of an active unit.
- A unit with active direct children cannot be deactivated.
- Deactivation is a soft status change; the row and historical references stay.

## Responses

- `200`: updated organizational unit, including current `is_active`
- `404 ORGANIZATIONAL_UNIT_NOT_FOUND`: target does not exist
- `409 UNIT_CODE_ALREADY_EXISTS`: duplicate supplied code
- `409 UNIT_HAS_ACTIVE_CHILDREN`: unsafe deactivation
- `422 VALIDATION_ERROR`: invalid fields, parent, or circular hierarchy

## Implementation

Pydantic handles partial-field validation and normalization. The existing
organizational-unit service checks uniqueness, parent validity, cycles, and
active children before one transaction updates the row.
