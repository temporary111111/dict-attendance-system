# List Admin Users Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Super Admin-only endpoint that lists safe admin account data.

**Architecture:** The existing users API module will query users with eager-loaded role and organizational unit relationships. One shared formatter and response schema will serve both create and list responses.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Pytest.

## Global Constraints

- Include active and inactive admin users.
- Never expose password hashes.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Admin User List

**Files:**
- Modify: `backend/tests/test_user_routes.py`
- Modify: `backend/app/schemas/users.py`
- Modify: `backend/app/api/users.py`

**Interfaces:**
- Consumes: SQLAlchemy `Session` and the existing `User` relationships.
- Produces: `GET /api/users` returning a list of safe admin user items.

- [x] Add failing tests for safe list output and authentication.
- [x] Run the focused tests and confirm GET is not yet allowed.
- [x] Add the list response schema and eager-loaded query.
- [x] Reuse a shared user formatter for create and list responses.
- [x] Run focused tests and the complete backend test suite.
