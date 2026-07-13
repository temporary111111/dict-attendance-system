# Create Organizational Unit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add secure creation of hierarchical DICT organizational units.

**Architecture:** Pydantic normalizes unit fields, a focused service validates parent and code constraints transactionally, and the existing reference-data API exposes the Super Admin-only POST route.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Pytest.

## Global Constraints

- Super Admin authentication is required.
- New units start active.
- Preserve flexible DICT unit types.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Organizational Unit Creation

**Files:**
- Modify: `backend/tests/test_reference_data_routes.py`
- Modify: `backend/app/schemas/reference_data.py`
- Create: `backend/app/services/organizational_unit_service.py`
- Modify: `backend/app/api/reference_data.py`

**Interfaces:**
- Consumes: `CreateOrganizationalUnitRequest` and SQLAlchemy `Session`.
- Produces: `POST /api/organizational-units` with standard success and errors.

- [x] Add failing tests for creation, validation, conflict, and authentication.
- [x] Run focused tests and confirm POST is not yet allowed.
- [x] Add normalized request and response schemas.
- [x] Add parent/code validation service and POST route.
- [x] Run focused tests and the complete backend test suite.
