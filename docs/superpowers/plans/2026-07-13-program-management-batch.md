# Program Management Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver all Program and Program Admin Assignment APIs in one verified backend batch.

**Architecture:** One shared schema module defines the API contracts, while separate services own program and assignment business rules. Two focused routers expose role-aware reads and Super Admin-only writes using the existing FastAPI dependency and response patterns.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, MySQL, Pytest.

## Global Constraints

- Program Admins only see actively assigned programs.
- Program and assignment deletion uses status changes, not row deletion.
- Existing database constraints remain unchanged.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Program API

**Files:**
- Create: `backend/tests/test_program_routes.py`
- Create: `backend/app/schemas/programs.py`
- Create: `backend/app/services/program_service.py`
- Create: `backend/app/api/programs.py`
- Modify: `backend/app/api/router.py`

**Interfaces:**
- Consumes: current admin user, SQLAlchemy session, program request schemas.
- Produces: list, create, detail, partial update, and archive/restore endpoints.

- [x] Add route tests for role visibility, writes, validation, conflicts, and auth.
- [x] Run tests and confirm the missing routes fail for the expected reason.
- [x] Implement schemas, program service, route mapping, and router registration.
- [x] Run focused tests until the Program API is green.

### Task 2: Program Admin Assignment API

**Files:**
- Create: `backend/tests/test_program_assignment_routes.py`
- Create: `backend/app/services/program_assignment_service.py`
- Create: `backend/app/api/program_assignments.py`
- Modify: `backend/app/schemas/programs.py`
- Modify: `backend/app/api/router.py`

**Interfaces:**
- Consumes: Super Admin user, program/user IDs, and assignment request schemas.
- Produces: assignment list, assign/reactivate, and idempotent revoke endpoints.

- [x] Add route tests for create, invalid references, duplicate active assignment, reactivation, listing, revocation, and auth.
- [x] Run tests and confirm the missing routes fail for the expected reason.
- [x] Implement assignment lifecycle service, route mapping, and registration.
- [x] Run all Batch 1 focused tests until green.

### Task 3: Documentation and Verification

**Files:**
- Modify: `backend/README.md`
- Verify: `others/backend/backend-api-plan.md`

**Interfaces:**
- Consumes: completed Batch 1 endpoint behavior.
- Produces: documented endpoints and fresh regression evidence.

- [x] Document Program and Assignment endpoints and key rules.
- [x] Run the complete backend test suite.
- [x] Review the implementation against the design and resolve gaps.
