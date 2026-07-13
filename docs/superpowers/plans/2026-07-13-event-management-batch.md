# Event Management Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver all Event, attendance-link/QR, and status lifecycle APIs in one verified batch.

**Architecture:** A focused event service owns authorization and lifecycle rules, while a separate QR service owns filesystem work. One event router exposes role-aware reads and writes using existing response and auth conventions.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, MySQL, qrcode, Pillow, Pytest.

## Global Constraints

- Program Admin operations require an active program assignment.
- Archived rows remain in the database.
- Public attendance URLs are configurable and event codes are unguessable.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Event CRUD and Access

**Files:**
- Create: `backend/tests/test_event_routes.py`
- Create: `backend/app/schemas/events.py`
- Create: `backend/app/services/event_service.py`
- Create: `backend/app/api/events.py`
- Modify: `backend/app/api/router.py`

- [x] Add failing tests for role-aware list/detail, create, update, validation, and auth.
- [x] Implement normalized schemas, access checks, event code generation, and routes.
- [x] Run focused tests until Event CRUD is green.

### Task 2: Attendance Link, QR, and Status

**Files:**
- Create: `backend/tests/test_qr_code_service.py`
- Modify: `backend/tests/test_event_routes.py`
- Create: `backend/app/services/qr_code_service.py`
- Modify: `backend/app/services/event_service.py`
- Modify: `backend/app/api/events.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`
- Modify: `backend/requirements.txt`
- Modify: `backend/.env.example`

- [x] Add failing tests for QR refresh, open, close, reopen, and archive rules.
- [x] Add configurable QR storage and static serving.
- [x] Implement QR generation, cleanup, and event transitions.
- [x] Run all Batch 2 focused tests until green.

### Task 3: Documentation and Verification

**Files:**
- Modify: `backend/README.md`
- Modify: `others/backend/backend-api-plan.md`

- [x] Document Event endpoints, configuration, and lifecycle rules.
- [x] Run the complete backend test suite.
- [x] Run the MySQL ORM smoke check and OpenAPI route audit.
- [x] Review the implementation against this design and resolve gaps.
