# Auth Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JWT access-token authentication for admin users.

**Architecture:** Password hashing and JWT helpers live in `app/core/security.py`.
Login business logic lives in `app/services/auth_service.py`. Request and
response shapes live in `app/schemas/auth.py`. Routes live in `app/api/auth.py`,
and reusable protected-route helpers live in `app/api/dependencies/auth.py`.

**Tech Stack:** FastAPI, SQLAlchemy, MySQL, bcrypt, PyJWT, Pytest.

## Global Constraints

- Use JWT access token only for MVP auth.
- Do not store access tokens in the database.
- Do not add refresh tokens yet.
- Only `super_admin` and `program_admin` users can log in.
- External attendees do not have login accounts.
- Follow the Taglish commenting guidelines in `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

## Tasks

- [ ] Add auth dependencies and settings.
- [ ] Add tested password hashing and JWT helpers.
- [ ] Add auth schemas.
- [ ] Add tested login/current-user service logic.
- [ ] Add auth route and dependency tests.
- [ ] Add `/api/auth/login`, `/api/auth/me`, and `/api/auth/logout`.
- [ ] Register auth routes and update backend docs.
- [ ] Run full backend tests and manual smoke checks.
