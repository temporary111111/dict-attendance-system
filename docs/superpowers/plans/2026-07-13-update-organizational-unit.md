# Update Organizational Unit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe partial updates for hierarchical DICT organizational units.

**Architecture:** Pydantic distinguishes omitted fields from explicit `null`, while the organizational-unit service owns hierarchy and status rules. The reference-data API maps domain errors to the project's standard response envelope.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Pytest.

## Global Constraints

- Super Admin authentication is required.
- Preserve historical rows through soft deactivation.
- Prevent circular or active-under-inactive hierarchy states.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Organizational Unit Update

**Files:**
- Modify: `backend/tests/test_reference_data_routes.py`
- Modify: `backend/app/schemas/reference_data.py`
- Modify: `backend/app/services/organizational_unit_service.py`
- Modify: `backend/app/api/reference_data.py`
- Modify: `backend/README.md`

**Interfaces:**
- Consumes: `UpdateOrganizationalUnitRequest`, path `org_unit_id`, and SQLAlchemy `Session`.
- Produces: `PATCH /api/organizational-units/{orgUnitId}` with standard success and error responses.

- [x] Add failing tests for partial updates, clearing fields, hierarchy safety, conflicts, and authentication.
- [x] Run focused tests and confirm the missing endpoint fails.
- [x] Add partial-update schemas with normalization.
- [x] Add hierarchy validation and transactional update service.
- [x] Expose the PATCH route and map domain errors.
- [x] Update backend endpoint documentation.
- [x] Run focused tests and the complete backend test suite.
