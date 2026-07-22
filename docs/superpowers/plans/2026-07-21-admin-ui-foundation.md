# Admin UI Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved modern DICT visual direction to the real admin workspace without changing its API behavior.

**Architecture:** Keep `admin.js` as the owner of existing views and API calls. Add a small shared theme module for system preference and browser persistence, then enhance the current admin shell through stable HTML hooks and CSS tokens.

**Tech Stack:** Vanilla HTML, CSS custom properties, browser `localStorage`, ES modules, Python `unittest` static checks.

## Global Constraints

- Preserve all existing API routes, view IDs, form fields, and role checks.
- Use current Material Symbols and local DICT assets; add no frontend dependency.
- Default theme follows the operating system, while a manual choice is remembered.
- Desktop sidebar is expanded by default and may collapse; mobile stays a drawer.
- Keep comments concise and Taglish only where behavior is not self-explanatory.

---

### Task 1: Regression coverage for theme and navigation

**Files:**
- Modify: `frontend/tests/test_ui_ux_regressions.py`

**Interfaces:**
- Consumes: static frontend source files.
- Produces: checks for theme controls, grouped navigation, persistence hooks, and collapsed-sidebar styling.

- [x] Add failing assertions for the approved UI contracts.
- [x] Run `python -m unittest frontend.tests.test_ui_ux_regressions -v` and confirm the new assertions fail.

### Task 2: Shared theme foundation

**Files:**
- Create: `frontend/js/theme.js`
- Modify: `frontend/css/base.css`
- Modify: `frontend/admin.html`

**Interfaces:**
- Produces: `initializeThemeToggle(button)` and semantic light/dark CSS tokens.

- [x] Implement system-default theme selection and persisted manual choice.
- [x] Add dark-compatible shared controls, focus states, and status tokens.
- [x] Add the accessible theme button to the admin top bar.

### Task 3: Modern admin shell

**Files:**
- Modify: `frontend/admin.html`
- Modify: `frontend/css/admin.css`
- Modify: `frontend/js/admin.js`

**Interfaces:**
- Consumes: existing view names and role-based visibility IDs.
- Produces: grouped navigation, compact dashboard surfaces, remembered desktop collapse, and unchanged mobile drawer behavior.

- [x] Restructure the sidebar into Overview, Operations, Administration, and Governance groups.
- [x] Add responsive collapsed-sidebar behavior with accessible labels and persistence.
- [x] Restyle all existing admin panels, tables, dialogs, forms, alerts, and responsive states using the shared tokens.
- [x] Keep every existing admin workflow functional.

### Task 4: Verification

**Files:**
- Verify only.

**Interfaces:**
- Consumes: completed admin UI foundation.
- Produces: static checks and browser evidence at desktop and mobile sizes.

- [x] Run `python -m unittest frontend.tests.test_ui_ux_regressions -v`.
- [x] Run `python frontend/scripts/smoke_check.py`.
- [x] Start the local frontend if needed and inspect light, dark, expanded, collapsed, and mobile states in a browser.
- [x] Check browser console errors and confirm existing navigation still renders.
