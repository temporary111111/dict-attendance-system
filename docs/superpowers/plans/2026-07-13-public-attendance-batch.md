# Public Attendance Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver fixed public attendance submission with PSGC validation, duplicate protection, and private signatures.

**Architecture:** Separate PSGC and signature services isolate reference queries and private file handling from the transactional attendance service. Two public routers expose event/submission and dropdown contracts without admin authentication.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, MySQL, Pillow, python-multipart, Pytest.

## Global Constraints

- No Google Forms or form builder.
- Event must be open before accepting attendance.
- Same email cannot submit twice to the same event.
- Signature images are private and never statically mounted.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Public Event and PSGC Lookups

**Files:**
- Create: `backend/tests/test_public_reference_routes.py`
- Create: `backend/app/schemas/public_attendance.py`
- Create: `backend/app/services/psgc_service.py`
- Create: `backend/app/api/psgc.py`
- Create: `backend/app/api/public_attendance.py`
- Modify: `backend/app/api/router.py`

- [x] Add failing tests for public event states and four active PSGC lookups.
- [x] Implement response schemas, filtered queries, routes, and registration.
- [x] Run focused public reference tests until green.

### Task 2: Attendance Submission and Signatures

**Files:**
- Create: `backend/tests/test_public_attendance_routes.py`
- Create: `backend/tests/test_signature_service.py`
- Create: `backend/app/services/public_attendance_service.py`
- Create: `backend/app/services/signature_service.py`
- Modify: `backend/app/schemas/public_attendance.py`
- Modify: `backend/app/api/public_attendance.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/requirements.txt`
- Modify: `backend/.env.example`

- [x] Add failing tests for valid submissions, duplicates, event status, consent, PSGC hierarchy, and images.
- [x] Add multipart dependency and private signature configuration.
- [x] Implement form parsing, validation, transactional persistence, and cleanup.
- [x] Run all Batch 3 focused tests until green.

### Task 3: Documentation and Verification

**Files:**
- Modify: `backend/README.md`
- Modify: `others/backend/backend-api-plan.md`

- [x] Document public endpoints, multipart fields, privacy, and address rules.
- [x] Run the complete backend test suite.
- [x] Run MySQL ORM smoke check, compilation, and six-route OpenAPI audit.
- [x] Review the implementation against this design and resolve gaps.
