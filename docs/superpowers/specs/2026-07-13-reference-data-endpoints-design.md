# Reference Data Endpoints Design

## Goal

Bigyan ang Super Admin ng read-only API para makuha ang roles at DICT
organizational units na gagamitin later sa paggawa ng admin user accounts.

## Endpoints

- `GET /api/roles`
- `GET /api/organizational-units`

Parehong nangangailangan ng active Super Admin JWT. Ang Program Admin at
requests na walang valid token ay hindi pinapayagan.

## Data Rules

- Active records lang ang ibabalik.
- Roles are ordered by `role_name`.
- Organizational units are ordered by `unit_name`.
- Kasama ang `parent_unit_id` para mabuo ng frontend ang office/division/unit
  hierarchy.
- Walang create, update, pagination, search, o inactive filter sa slice na ito.

## Response Shape

Susunod ang endpoints sa existing `{ "data": ..., "message": "..." }`
success response. Role items contain `role_id`, `role_name`, and `description`.
Organizational unit items contain `org_unit_id`, `parent_unit_id`, `unit_name`,
`unit_type`, and `unit_code`.

## Implementation

Simple SQLAlchemy queries ang ilalagay diretso sa focused reference-data route
module. Hindi muna kailangan ng service abstraction dahil wala pang business
workflow bukod sa active filtering at sorting.

