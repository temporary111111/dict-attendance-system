# Reference Data Endpoints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Super Admin-only read endpoints for active roles and organizational units.

**Architecture:** A focused API module will query the existing SQLAlchemy models and return the project's standard response envelope. Pydantic schemas will document and validate each endpoint's output.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Pytest.

## Global Constraints

- Active records only.
- Alphabetical ordering by role or unit name.
- Super Admin authentication is required.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Roles and Organizational Units

**Files:**
- Create: `backend/tests/test_reference_data_routes.py`
- Create: `backend/app/schemas/reference_data.py`
- Create: `backend/app/api/reference_data.py`
- Modify: `backend/app/api/router.py`

**Interfaces:**
- Consumes: `Session`, `Role`, `OrganizationalUnit`, and `require_super_admin`.
- Produces: `GET /api/roles` and `GET /api/organizational-units`.

- [x] Write route tests for successful responses and required authentication.
- [x] Run the focused tests and confirm the routes return `404` before implementation.
- [x] Add Pydantic response schemas.
- [x] Add active, alphabetically sorted SQLAlchemy queries and register the router.
- [x] Run the focused tests, then the complete backend test suite.
