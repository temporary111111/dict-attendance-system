# Admin User Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe activation and deactivation for admin accounts without deleting records.

**Architecture:** A literal-valued request schema restricts status values. The user service receives actor and target IDs, prevents self-deactivation, validates reactivation eligibility, and performs the transaction.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Pytest.

## Global Constraints

- Super Admin authentication is required.
- Never hard delete a user for deactivation.
- Never expose password hashes.
- Follow `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Admin Account Status

**Files:**
- Modify: `backend/tests/test_user_routes.py`
- Modify: `backend/app/schemas/users.py`
- Modify: `backend/app/services/user_service.py`
- Modify: `backend/app/api/users.py`

**Interfaces:**
- Consumes: target `user_id`, actor `user_id`, and `account_status`.
- Produces: `PATCH /api/users/{user_id}/status` with safe account data or standard errors.

- [x] Add failing tests for transitions, validation, lockout protection, and auth.
- [x] Run focused tests and confirm the status route is missing.
- [x] Add status request/response schemas.
- [x] Add service transition rules and the authenticated route.
- [x] Run focused tests and the complete backend test suite.
