# Create Admin User Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested Super Admin-only endpoint for creating secure admin accounts.

**Architecture:** Pydantic validates request structure, a focused service validates database references and creates the user transactionally, and the API route maps domain failures to standard HTTP errors. A shared FastAPI validation handler keeps all field errors in the project's standard response shape.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, email-validator, bcrypt, Pytest.

## Global Constraints

- JWT Super Admin authentication is required.
- Never store or return a plain password.
- Normalize stored email to lowercase.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Create Admin User Endpoint

**Files:**
- Create: `backend/tests/test_user_routes.py`
- Create: `backend/app/schemas/users.py`
- Create: `backend/app/services/user_service.py`
- Create: `backend/app/api/users.py`
- Modify: `backend/app/core/exceptions.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/router.py`
- Modify: `backend/requirements.txt`

**Interfaces:**
- Consumes: `CreateUserRequest`, SQLAlchemy `Session`, active roles and units.
- Produces: `POST /api/users` with `201`, `409`, and standardized `422` responses.

- [ ] Add endpoint tests for success, auth, duplicate email, invalid references, and request validation.
- [ ] Run the focused tests and confirm they fail with `404` before implementation.
- [ ] Add and install the email validation dependency.
- [ ] Add request and response schemas plus standard validation-error handling.
- [ ] Add the tested creation service and route, then register the router.
- [ ] Run focused tests and the complete backend test suite.

