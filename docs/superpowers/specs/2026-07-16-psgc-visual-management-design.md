# PSGC Visual Management Design

## Goal

Give Super Admins a practical visual way to inspect and maintain local PSGC lookup data without opening MySQL. The feature follows core master-data practices but remains focused on the attendance system.

## Scope

The existing `PSGC Data` page will become a reference-data workspace with these capabilities:

1. Browse the local hierarchy in order: region, province, city/municipality, then barangay.
2. Search an active or inactive PSGC row by official code or name.
3. Inspect one selected row and its location in the hierarchy.
4. Edit a verified local name correction, with a required reason and audit log.
5. Correct a code only through a controlled action with validation, impact information, confirmation, and audit log.
6. Deactivate and restore rows instead of using deletion as the ordinary action.
7. Permanently delete only a record with no child records and no attendance-address reference.

The existing PSA Excel preview-and-import workflow remains the normal way to update official PSGC data. Manual maintenance is an exception workflow for verified local corrections.

## Explicit Non-Goals

This version does not add a PSA API dependency, approval workflow, separate data-steward role, import-batch table, effective dates, replacement-code mapping, rollback system, or a large expandable tree containing every barangay.

## User Experience

### PSGC Workspace

The Super Admin-only page contains:

* A global search field for an official PSGC code or name.
* A breadcrumb such as `PSGC Data / Region V / Albay`.
* One current-level table with code, official name, geographic type, status, and an inspect action.
* A page-size control and pagination. No request returns the entire barangay table.
* A details panel or dialog for the selected row.

Opening the page shows regions. Selecting a region shows its provinces and direct city/municipality records. Selecting a province shows its cities/municipalities. Selecting a city or municipality shows its barangays. The current table includes inactive records only when the Super Admin enables the status filter.

Search results show each matching row's full location, for example `Region V > Albay > City of Legazpi`, so a result remains understandable outside the drill-down view.

### Row Actions

The row details view shows the official code, name, parent location, status, child count, and attendance-address reference count.

`Edit details` changes a name only. The reason is required and is stored in the audit log.

`Correct code` is separate from normal edit. It requires a numeric, unique 10-digit code, a reason, and a confirmation that displays the number of directly affected references. To keep this version safe and small, code correction is available only when the row has no child records and no attendance-address reference. If it has a dependency, the UI explains that a corrected PSA import is the correct path.

`Deactivate` hides the selected row from new public address selections. `Restore` makes it active again. Neither action removes historical records.

`Permanently delete` appears only when the selected row has no child records and no attendance-address reference. It uses a clear confirmation dialog. A row that fails either check can be deactivated but cannot be deleted.

Parent hierarchy corrections remain import-led in this version. The UI displays the parent for review, but it does not provide a free-form parent move action. This avoids silently breaking child records or historical addresses. A verified official hierarchy correction is applied through a corrected PSA import.

## Backend Design

New protected `/api/admin/psgc` read routes provide paginated current-level data, global search, and one record detail. They use Super Admin authorization and return only the requested level.

New write routes provide name correction, controlled code correction, status change, and safe permanent deletion. Each write validates the existing normalized hierarchy, wraps database changes in one transaction, and creates a specific audit log record with old values, new values, reason, and impact counts.

The existing manual create/upsert routes remain available for now but are no longer the primary user workflow. They must follow the same audit and parent validation rules.

## Data Rules

* `is_active` remains the soft-deactivation field.
* A PSGC code remains a 10-digit numeric identifier.
* A code correction cannot create a duplicate primary key.
* Code correction is blocked when a row has a child row or an attendance-address reference.
* Hard deletion is blocked under the same dependency rule.
* Every direct manual correction requires a non-empty reason.
* PSA imports stay the source-of-truth path for bulk official changes, renames, code revisions, and hierarchy revisions.
* Existing attendance addresses are never deleted by PSGC management actions.

## API Shapes

The exact response schemas follow the current standard `{ data, message }` pattern.

* `GET /api/admin/psgc/regions?page=&pageSize=&status=&search=`
* `GET /api/admin/psgc/regions/{regionCode}/children?page=&pageSize=&status=`
* `GET /api/admin/psgc/provinces/{provinceCode}/children?page=&pageSize=&status=`
* `GET /api/admin/psgc/cities-municipalities/{cityMunicipalityCode}/children?page=&pageSize=&status=`
* `GET /api/admin/psgc/search?query=&level=&status=&page=&pageSize=`
* `GET /api/admin/psgc/{level}/{code}`
* `PATCH /api/admin/psgc/{level}/{code}/name`
* `PATCH /api/admin/psgc/{level}/{code}/status`
* `PATCH /api/admin/psgc/{level}/{code}/code`
* `DELETE /api/admin/psgc/{level}/{code}`

`level` is restricted to `region`, `province`, `city_municipality`, or `barangay`. No route accepts a user-provided SQL table name.

## Error Handling

The UI keeps the current table unchanged when an action fails and displays the returned API error. Dependency blocks return a clear error code and counts, such as child records or attendance-address references. A stale code or a duplicate code returns a validation error. Unauthorized users receive the existing role-based authorization response.

## Testing

Backend tests cover:

* Super Admin authorization for every new route.
* Pagination and status filtering by PSGC level.
* Search by name and code, including full hierarchy location.
* Name correction and audit log reason.
* Code correction success for a dependency-free row.
* Code correction rejection for duplicate, child-dependent, and attendance-referenced rows.
* Deactivate, restore, hard-delete success, and hard-delete rejection rules.

Frontend verification covers drill-down navigation, search result navigation, edit form validation, confirmation dialogs, inactive filtering, and blocked-action messages.

## Documentation Impact

Update the frontend manual test guide, backend API documentation, database PSGC import plan, and data dictionary only where behavior changes. Do not update DFD or ERD images for this feature.
