# Swagger Bearer Authorize Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan.

**Goal:** Make Swagger's `Authorize` dialog accept the JWT access token used by the JSON login endpoint.

**Architecture:** Keep `POST /api/auth/login` unchanged. Replace the OAuth2 password-flow dependency with FastAPI `HTTPBearer`, then pass its extracted token string to the existing JWT validation code.

**Tech Stack:** FastAPI, PyJWT, Pytest.

## Global Constraints

- Keep the JSON login request unchanged.
- Keep the `Authorization: Bearer <token>` request format.
- Keep the existing standardized authentication errors.
- Follow the Taglish commenting guidelines in `docs/commenting-guidelines.md`.
- Do not make git commits; Sofia handles version control.

---

### Task 1: Swagger Bearer Security Scheme

**Files:**
- Modify: `backend/tests/test_auth_routes.py`
- Modify: `backend/app/api/dependencies/auth.py`

**Interfaces:**
- Consumes: JWT string from the HTTP `Authorization` header.
- Produces: an OpenAPI HTTP Bearer security scheme and the same validated `User` dependency.

- [ ] Add an OpenAPI test requiring an HTTP Bearer security scheme.
- [ ] Run the focused test and confirm it fails against the current OAuth2 scheme.
- [ ] Replace `OAuth2PasswordBearer` with `HTTPBearer` and extract `credentials.credentials`.
- [ ] Run auth tests, then the complete backend test suite.
