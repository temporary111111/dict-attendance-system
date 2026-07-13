# Admin User Detail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Super Admin-only endpoint for retrieving one safe admin account record.

**Architecture:** The existing users route will perform a direct eager-loaded query by user ID, reuse the safe formatter, and return a standard not-found error when needed.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Pytest.

## Global Constraints

- Super Admin authentication is required.
- Never expose password hashes.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Admin User Detail

**Files:**
- Modify: `backend/tests/test_user_routes.py`
- Modify: `backend/app/schemas/users.py`
- Modify: `backend/app/api/users.py`

**Interfaces:**
- Consumes: positive `user_id` and SQLAlchemy `Session`.
- Produces: `GET /api/users/{user_id}` with `200`, `401`, or `404`.

- [x] Add failing tests for success, not found, and authentication.
- [x] Run focused tests and confirm the detail route returns `404` before implementation.
- [x] Add the detail response schema and eager-loaded lookup route.
- [x] Run focused tests and the complete backend test suite.
