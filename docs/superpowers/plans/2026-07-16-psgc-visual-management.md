# PSGC Visual Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Super Admin a clear PSGC workspace where they can browse the local reference data, search it, correct verified local names/codes safely, deactivate or restore records, and permanently delete only records that have no hierarchy or attendance-address dependency.

**Architecture:** Extend the existing FastAPI `/api/admin/psgc` module with a focused PSGC-management service and response schemas. The service is the single place that validates level-specific hierarchy, calculates dependencies, performs guarded mutations, and writes audit logs. Replace the current manual PSGC form in the vanilla-JS admin page with a drill-down workspace that loads one page of data at a time.

**Tech Stack:** Python 3, FastAPI, SQLAlchemy, Pydantic, MySQL 8, pytest, vanilla HTML/CSS/JavaScript.

## Global Constraints

- Only Super Admin may use every route and screen in this plan.
- Keep the existing PSA workbook import as the normal source of truth. This feature is for verified local corrections and review, not an alternative bulk-import system.
- No schema migration is needed. Reuse the four PSGC tables and the existing `audit_logs` table.
- Do not add a live PSA API integration, approval workflow, data-steward role, batch history table, effective dating, rollback feature, replacement mapping, or free-form parent-moving workflow.
- Every manual name/code/status/delete action requires an audit reason. Use short, clear Taglish comments only where code needs orientation.
- A PSGC code correction and permanent delete are allowed only when the record has no child records and no `attendance_record_addresses` reference. Return a structured conflict response with the dependency counts when blocked.
- Deactivation/restoration is the normal removal action. It does not remove the row or past attendance history.
- Do not fetch the entire PSGC dataset into the browser. Every browse/search API is paginated, `pageSize` is capped at 100, and the UI requests only the current result page.
- Preserve the current LAN-friendly static frontend and FastAPI backend setup. Do not introduce a frontend framework.
- Do not update DFD/ERD diagram images.
- The user owns Git/version control. Do not run Git commands or create commits.

---

## API Contract

All responses use the existing `success_response` envelope. All routes below are under `/api/admin/psgc` and require `require_super_admin`.

### Read routes

| Route | Purpose |
| --- | --- |
| `GET /regions?page=&pageSize=&status=&search=` | Paginated top-level region list. |
| `GET /regions/{regionCode}/children?page=&pageSize=&status=&search=` | Paginated union of the region's provinces and direct city/municipality records with no province. |
| `GET /provinces/{provinceCode}/children?page=&pageSize=&status=&search=` | Paginated city/municipality list under a province. |
| `GET /cities-municipalities/{cityMunicipalityCode}/children?page=&pageSize=&status=&search=` | Paginated barangay list under a city/municipality. |
| `GET /search?query=&level=&status=&page=&pageSize=` | Global paginated search across one or all levels. Each result includes its full hierarchy label. |
| `GET /{level}/{code}` | Detail data, hierarchy path, active state, and dependency counts for the selected row. |

`level` is a validated enum: `region`, `province`, `city_municipality`, or `barangay`. List rows contain `level`, `code`, `name`, `isActive`, `parentLabel` where applicable, and city/municipality type where applicable. Detail includes `childCount` and `attendanceAddressReferenceCount`.

### Write routes

| Route | Body | Rule |
| --- | --- | --- |
| `PATCH /{level}/{code}/name` | `name`, `reason` | Correct the local display name and audit old/new values. |
| `PATCH /{level}/{code}/status` | `isActive`, `reason` | Deactivate or restore a local record and audit old/new values. |
| `PATCH /{level}/{code}/code` | `newCode`, `reason`, confirmation flag | New code must be numeric, exactly 10 digits, unique at its level, and the record must have no children or attendance-address reference. |
| `DELETE /{level}/{code}` | `reason`, confirmation flag | Permanently remove only a dependency-free record; otherwise return `409 PSGC_RECORD_IN_USE`. |

All mutation routes return the fresh detail record. Code/deletion conflict responses include `childCount` and `attendanceAddressReferenceCount` so the UI can explain why the action is unavailable.

## Implementation Tasks

### Task 1: Add PSGC management request and response schemas

**Files:**
- Create: `backend/app/schemas/psgc_management.py`
- Modify: `backend/app/schemas/__init__.py` only if this package currently exports schemas explicitly
- Test: `backend/tests/test_psgc_management_schemas.py`

- [ ] Define `PSGCLevel` and status-filter literals/enums rather than accepting arbitrary table names.
- [ ] Define shared pagination (`page`, `pageSize`) with a lower bound of 1 and an upper limit of 100. Follow the project convention of accepting `pageSize` as the public query parameter.
- [ ] Define list/detail/path/dependency response models using the frontend naming convention (`isActive`, `childCount`, `attendanceAddressReferenceCount`).
- [ ] Define `PsgcNameUpdateRequest`, `PsgcStatusUpdateRequest`, `PsgcCodeUpdateRequest`, and `PsgcDeleteRequest`. Each requires a trimmed reason; the code/delete requests require an explicit confirmation boolean.
- [ ] Make a new-code validator strictly accept exactly ten numeric digits. Do not weaken the existing import/upsert schema merely to support this feature.

**Tests:**
- Valid 10-digit code and required reason are accepted.
- Non-numeric, short, or long replacement codes are rejected.
- Unsupported PSGC level, invalid pagination, and missing confirmation are rejected.

**Verification:**
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_psgc_management_schemas.py -q
```

### Task 2: Implement one PSGC management service with hierarchy and dependency guards

**Files:**
- Create: `backend/app/services/psgc_management_service.py`
- Modify: `backend/app/services/__init__.py` only if the package currently exports services explicitly
- Test: `backend/tests/test_psgc_management_service.py`

- [ ] Build a small internal level registry mapping the validated level to its SQLAlchemy model, code column, name column, parent information, and display label. Never resolve a model from untrusted client input.
- [ ] Implement paginated region, region-child, province-child, and city-child reads. The region-child read must include both provinces and direct city/municipality rows, while preserving a stable sort by name then code.
- [ ] Implement global search by code/name across the requested level or all levels. Include a readable full location path but do not load every row into Python before pagination.
- [ ] Implement selected-record detail with its complete hierarchy path, status, city/municipality type when relevant, child count, and attendance-address reference count.
- [ ] Implement a single dependency-count helper. Count immediate PSGC children for the selected level and direct `AttendanceRecordAddress` usage of that level's code.
- [ ] Implement `update_name`, `update_status`, `update_code`, and `delete_record`. All must load the record through the level registry, produce an audit log using `build_audit_log`, commit atomically, and return refreshed detail data.
- [ ] Block code changes and permanent deletion before mutation if either dependency count is nonzero. Raise a domain exception that retains both counts for API translation.
- [ ] Do not permit parent changes. A hierarchy issue stays an import-led correction in this version.

**Tests:**
- Region child listing includes both normal provinces and province-less cities/municipalities.
- Search can find a record by code and by partial name while respecting level/status filters and pagination.
- Detail reports a hierarchy path and the two dependency counts correctly.
- Name and status edits store the intended fields and create audit logs with the supplied reason.
- Code update succeeds only for a unique, dependency-free record.
- Code update and delete are blocked for a record with child rows or attendance-address references, without modifying the record.
- Permanent delete succeeds only for a dependency-free record and creates an audit log.

**Verification:**
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_psgc_management_service.py -q
```

### Task 3: Expose the guarded PSGC management routes

**Files:**
- Modify: `backend/app/api/psgc_admin.py`
- Test: `backend/tests/test_psgc_management_routes.py`

- [ ] Add the read/write routes from the API contract while preserving the existing `/imports`, `/summary`, and manual-create endpoints.
- [ ] Place literal/static routes before parameterized `/{level}/{code}` routes so FastAPI cannot treat `search` or `regions` as a PSGC level.
- [ ] Translate not-found records to the project-standard `404` error envelope.
- [ ] Translate dependency guard failures to a project-standard `409` error envelope with code `PSGC_RECORD_IN_USE` and both count values in `details`.
- [ ] Return `422` validation errors through the app's existing validation-response format.
- [ ] Confirm every new route depends on `require_super_admin`; do not rely on hiding the frontend navigation as authorization.

**Tests:**
- Unauthenticated and Program Admin calls are denied.
- Super Admin can paginate a level, search, and read one record's details.
- Super Admin can correct a name and toggle status with a reason.
- Dependency-blocked code correction/delete return `409` and dependency values.
- Invalid level and invalid 10-digit-code body return a validation response.

**Verification:**
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_psgc_admin_routes.py backend/tests/test_psgc_management_routes.py -q
```

### Task 4: Protect the existing import and public address behavior with regression tests

**Files:**
- Modify: `backend/tests/test_psgc_import_service.py`
- Modify: `backend/tests/test_psgc_admin_routes.py`
- Modify: the existing PSGC/public-address test module discovered in `backend/tests/`

- [ ] Preserve the tested PSA Revision 1 province-parent code behavior that fixed the Albay city/municipality issue.
- [ ] Assert that the existing import preview/apply routes still work after router changes.
- [ ] Assert the public PSGC address lookup continues to filter city/municipality choices by the selected province code and returns only active rows.
- [ ] Do not add code that changes an address already stored in attendance records; PSGC management affects reference rows only.

**Verification:**
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_psgc_import_service.py backend/tests/test_psgc_admin_routes.py backend/tests -q
```

### Task 5: Replace the manual PSGC panel with a browse-first Super Admin workspace

**Files:**
- Modify: `frontend/js/admin.js`
- Modify: `frontend/css/admin.css`

- [ ] Keep the existing import panel and import preview workflow at the top of the PSGC view.
- [ ] Replace the manual create/update form with a workspace containing: search, level filter, active/inactive filter, breadcrumb, current-level table, pagination controls, and a details dialog/panel.
- [ ] Start at Regions. Selecting a region, province, or city/municipality updates the breadcrumb and requests only the next level's current page. Show direct city/municipality records clearly when a region has them.
- [ ] Use existing frontend helpers (`apiRequest`, `renderLoading`, `renderError`, `openDialog`, `showToast`, and `setButtonBusy`) rather than adding a new client-side framework or duplicate request layer.
- [ ] Render inactive rows with a restrained inactive state. In the details action area, make `Deactivate`/`Restore` the normal action; make permanent delete visually secondary and confirmation-gated.
- [ ] Provide separate dialogs for: name correction with reason, status change with reason, code correction with replacement code/reason/confirmation, and permanent delete with reason/confirmation. Fetch current detail before showing action availability.
- [ ] When the API reports dependencies, show a clear message such as “May 3 child locations at 2 attendance address records, kaya hindi puwedeng baguhin o burahin ang code.” Do not guess from list data.
- [ ] Do not offer a parent selector or manual hierarchy move.
- [ ] Preserve responsive behavior at desktop and mobile widths. Use table overflow or a focused detail panel instead of squeezing labels into unreadable controls.

**Manual browser checks:**
- From the Super Admin account, browse Region V -> Albay and confirm city/municipality records appear for its provinces after the corrected import.
- Search a known barangay code and confirm its full path is visible.
- Deactivate then restore a safe test row and observe the filtered state changes.
- Attempt code correction/delete on a referenced row and confirm the message explains the block.
- Confirm Program Admin has no PSGC management navigation and cannot call the routes directly.

### Task 6: Update user-facing and technical documentation

**Files:**
- Modify: `frontend/manual-test-guide.md`
- Modify: `backend/README.md`
- Modify: `others/database/psgc-import-plan.md`

- [ ] Add a concise manual test flow for visual browse, search, name correction, deactivate/restore, dependency-blocked code/delete, and safe permanent delete.
- [ ] Document the new admin route group, permissions, pagination limit, and conflict behavior in the backend README.
- [ ] Update the PSGC operational document to say that PSA reimport remains the normal correction path; manual correction is a verified, audited local exception; parent changes remain import-led.
- [ ] State explicitly that inactive PSGC data remains in the database for history, while public attendance selectors use active rows only.

### Task 7: Run focused and full verification

**Files:**
- No production file changes expected unless verification identifies a defect.

- [ ] Run all new PSGC-management tests first, then the full backend test suite.
- [ ] Run the existing frontend static smoke check.
- [ ] With the existing LAN servers, perform a real Super Admin browser check for the full browse/search/action flow. Do not start duplicate servers unless the current servers are unavailable.
- [ ] Check browser console/network errors and confirm all table text fits at a narrow mobile viewport and a standard desktop viewport.
- [ ] Report the exact verification commands and results. Do not claim completion until these checks pass.

**Verification:**
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests -q
backend\.venv\Scripts\python.exe frontend/scripts/smoke_check.py
```

## Acceptance Criteria

- A Super Admin can inspect the local PSGC hierarchy without using MySQL directly.
- The UI stays organized: current level only, breadcrumb navigation, paginated results, and global search.
- Name corrections, status changes, code changes, and permanent deletions are auditable and require a reason.
- Code changes and permanent deletion cannot break the hierarchy or attendance-address history.
- Deactivation/restoration is available even when a row is used, and inactive rows are excluded from public attendance address selection.
- Existing PSA import and public address workflows keep their current behavior, including the fixed Region V/Albay city lookup.
- No DFD/ERD images, database migrations, or Git operations are introduced.
