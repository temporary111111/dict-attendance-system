# Project Documentation Guide

Use this order kapag may magkaibang guidance sa project files:

1. Approved current project decisions.
2. `database/schema.sql`, SQLAlchemy models, at passing backend tests.
3. `mvp-requirements-v1.md`, `system-process-flow.md`,
   `user-roles-and-permission-matrix.md`, at `backend/backend-api-plan.md`.
4. Current DFD and ERD sources plus their generated visuals.
5. `docs/superpowers/specs/` and `docs/superpowers/plans/` as implementation
   history for individual features.
6. Handoff and scratch files as historical context only.

## Current Decisions

- FastAPI API-only backend, MySQL, and SQLAlchemy.
- Stateless JWT access token for admin authentication.
- No Google Forms integration and no dynamic form builder.
- Fixed public attendance fields with optional PSGC address collection.
- Either typed or uploaded signature is required; image files are private.
- Super Admin sees all attendance records.
- Program Admin sees and reviews attendance only under actively assigned
  programs.
- Attendance records are never hard deleted; review uses `valid`, `duplicate`,
  `invalid`, or `void` status with an audit log.
- The DICT attendance sheet is generated output, not a runtime-imported entity.

## Historical Files

`handoff.txt`, `dict-attendance-system-handoff.md`, and
`system-requirements-scratch.txt` preserve earlier analysis. Their unresolved
questions do not override decisions already implemented and documented above.
