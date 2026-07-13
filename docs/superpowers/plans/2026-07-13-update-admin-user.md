# Update Admin User Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a secure partial-update endpoint for admin user profiles and organizational assignments.

**Architecture:** Pydantic will validate partial request semantics. The user service will reuse centralized email, role, and unit rules, perform one transaction, and return safe related data to the route.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Pytest.

## Global Constraints

- Super Admin authentication is required.
- Password and account status are outside this endpoint.
- Never expose password hashes.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Admin User Profile Update

**Files:**
- Modify: `backend/tests/test_user_routes.py`
- Modify: `backend/app/schemas/users.py`
- Modify: `backend/app/services/user_service.py`
- Modify: `backend/app/api/users.py`

**Interfaces:**
- Consumes: positive `user_id`, `UpdateUserRequest`, and SQLAlchemy `Session`.
- Produces: `PATCH /api/users/{user_id}` with safe updated user data or standard errors.

- [x] Add failing tests for update success and all documented errors.
- [x] Run focused tests and confirm PATCH is not yet allowed.
- [x] Add partial-update request and response schemas.
- [x] Centralize and reuse create/update validation in the user service.
- [x] Add the PATCH route and map service errors.
- [x] Run focused tests and the complete backend test suite.
