# Operational Documentation Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the operational project documentation with the implemented optional program-logo workflow.

**Architecture:** Update only documents used for setup, operations, manual testing, and database maintenance. Verify every statement against the current FastAPI settings, routes, frontend behavior, schema, and migrations; preserve historical records unchanged.

**Tech Stack:** Markdown, FastAPI settings and routes, vanilla frontend, MySQL schema.

## Global Constraints

- Use current code and schema as the source of truth.
- Do not change production code, LAN host configuration, pre-existing historical specs/plans, or the handoff document.
- Keep explanations simple and use the existing English/Taglish documentation style.
- The user manages Git; do not run Git commands or create commits.

---

### Task 1: Update Backend And Database Operations Docs

**Files:**
- Modify: `backend/README.md`
- Modify: `backend/.env.example`
- Modify: `others/database/README.md`
- Modify: `others/database/data-dictionary.md`

**Interfaces:**
- Consumes: `backend/app/core/config.py`, `backend/app/api/programs.py`, `backend/app/main.py`, `others/database/schema.sql`, and `others/database/migrations/`.
- Produces: Accurate configuration, API behavior, migration, and schema guidance for maintainers.

- [x] Document that Super Admin program create/update requests accept multipart logo uploads and return `logo_url`.
- [x] Document optional PNG/JPEG logos, the 2 MiB limit, public program-logo media path, and their public-form/PDF use.
- [x] Add `PROGRAM_LOGO_DIRECTORY`, `PROGRAM_LOGO_MAX_BYTES`, and `PROGRAM_LOGO_URL_PREFIX` to `.env.example` using current defaults.
- [x] Replace the single migration example with the chronological list for attendance field settings, field visibility, and program logos.
- [x] Add the nullable `programs.logo_path` dictionary entry.
- [x] Verify with `rg` that all three configuration names, `logo_path`, and all three migration filenames appear in the intended files.

### Task 2: Update Frontend And Project Operations Docs

**Files:**
- Modify: `frontend/README.md`
- Modify: `frontend/manual-test-guide.md`
- Modify: `others/README.md`

**Interfaces:**
- Consumes: `frontend/js/config.js`, `frontend/js/admin.js`, `frontend/js/attendance.js`, and `frontend/attendance.html`.
- Produces: Accurate admin workflow, manual verification steps, and top-level current decisions.

- [x] Add optional program-logo support to the frontend capabilities list.
- [x] Explain that `apiBaseUrl` is environment-specific and must point to the running backend; preserve the current `.131` example because it matches `config.js`.
- [x] Add manual test steps for upload, replacement, removal, public attendance header display, and PDF display of a valid program logo.
- [x] Add a current-decision note that program logos are optional and are shown on the public form and PDF when configured.
- [x] Verify with `rg` that current `.131`, PNG/JPEG, 2 MiB, public-form/PDF behavior, and all manual test operations are documented.

### Task 3: Cross-Check Documentation Claims

**Files:**
- Verify: `backend/README.md`
- Verify: `backend/.env.example`
- Verify: `frontend/README.md`
- Verify: `frontend/manual-test-guide.md`
- Verify: `others/database/README.md`
- Verify: `others/database/data-dictionary.md`
- Verify: `others/README.md`

**Interfaces:**
- Consumes: Updated operational documentation and the current implementation files named in Tasks 1 and 2.
- Produces: A reviewed operational-documentation set without stale program-logo or configuration guidance.

- [x] Compare every program-logo setting, upload constraint, media URL, schema field, and migration filename with source code.
- [x] Confirm that no pre-existing historical plans, historical specs, or handoff document were modified.
- [x] Run `python frontend\scripts\smoke_check.py` to ensure the documentation work did not accidentally break frontend references.
