# Login and Public Attendance UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** I-refresh ang admin login at public attendance pages gamit ang approved compact DICT design at magkahiwalay na dark-mode preferences.

**Architecture:** Palalawakin ang existing `theme.js` para tumanggap ng explicit storage key. Ang login at admin ay gagamit ng admin key, habang ang public attendance ay gagamit ng public key. Mananatili ang kasalukuyang login at attendance JavaScript workflow; page shell, icons, theme initialization, at CSS presentation lamang ang babaguhin.

**Tech Stack:** Vanilla HTML, CSS, JavaScript ES modules, Python `unittest` static regressions, Chrome browser audit.

## Global Constraints

- Walang backend, database, API contract, consent wording, field requirement, signature, o submission behavior change.
- Walang bagong frontend dependency.
- Maximum 8px ang component border radius; walang gradient, decorative orb, o nested cards.
- Taglish comments lamang at ilalagay lang kapag hindi self-explanatory ang behavior.
- Huwag magpatakbo ng Git commands; user ang may hawak ng version control.
- Dapat walang page-level horizontal overflow sa 390px viewport.

## File Map

- Modify `frontend/js/theme.js`: reusable theme controller na may explicit storage key.
- Modify `frontend/js/admin.js`: explicit admin theme key.
- Modify `frontend/index.html`, `frontend/js/login.js`, `frontend/css/login.css`: login shell, icons, at admin theme toggle.
- Modify `frontend/attendance.html`, `frontend/js/attendance.js`, `frontend/css/attendance.css`: public header, public theme toggle, at form presentation.
- Modify `frontend/tests/test_ui_ux_regressions.py`: static regression safeguards.
- Use `frontend/scripts/smoke_check.py`: local-reference and HTML checks.

---

### Task 1: Isolated Theme Preferences

**Files:**
- Modify: `frontend/tests/test_ui_ux_regressions.py`
- Modify: `frontend/js/theme.js`
- Modify: `frontend/js/admin.js`

**Interfaces:**
- Produces: `THEME_STORAGE_KEYS.admin`, `THEME_STORAGE_KEYS.public`, at `initializeThemeToggle(button, storageKey)`.
- Consumes: browser `localStorage` at `matchMedia("(prefers-color-scheme: dark)")`.

- [ ] **Step 1: Write the failing regression test**

Add a test asserting that `theme.js` defines `dict-attendance-admin-theme` and `dict-attendance-public-theme`, accepts a `storageKey`, and no longer uses the shared `dict-attendance-theme` key.

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m unittest frontend.tests.test_ui_ux_regressions.UiUxRegressionTests.test_admin_and_public_themes_use_separate_storage_keys -v`

Expected: FAIL because the two storage keys do not exist yet.

- [ ] **Step 3: Implement the reusable controller**

Use this public interface in `theme.js`:

```javascript
export const THEME_STORAGE_KEYS = Object.freeze({
  admin: "dict-attendance-admin-theme",
  public: "dict-attendance-public-theme",
});

export function initializeThemeToggle(button, storageKey) {
  // Existing system fallback, button labels, icon update, at storage guards.
}
```

All read/write helpers must receive `storageKey`. Remove the module-level theme application that implicitly reads one shared key. Update `admin.js` to call:

```javascript
initializeThemeToggle(themeToggle, THEME_STORAGE_KEYS.admin);
```

- [ ] **Step 4: Run tests and JS syntax checks**

Run:

```powershell
python -m unittest frontend.tests.test_ui_ux_regressions -v
node --check frontend\js\theme.js
node --check frontend\js\admin.js
```

Expected: all tests pass and both Node checks exit `0`.

---

### Task 2: Compact DICT Login Page

**Files:**
- Modify: `frontend/tests/test_ui_ux_regressions.py`
- Modify: `frontend/index.html`
- Modify: `frontend/js/login.js`
- Modify: `frontend/css/login.css`

**Interfaces:**
- Consumes: `initializeThemeToggle(themeToggle, THEME_STORAGE_KEYS.admin)` from Task 1.
- Preserves: `#login-form`, all existing input IDs, validation, `saveSession`, `requireGuest`, at backend health check.

- [ ] **Step 1: Write failing login UI regressions**

Assert that `index.html` has `color-scheme="light dark"`, `#login-theme-toggle`, a Material Symbol password icon, and accessible labels. Assert that `login.js` initializes the admin theme key.

- [ ] **Step 2: Run the login-specific test and verify RED**

Run: `python -m unittest frontend.tests.test_ui_ux_regressions.UiUxRegressionTests.test_login_uses_admin_theme_and_accessible_icon_controls -v`

Expected: FAIL because the theme control and icon markup are missing.

- [ ] **Step 3: Update login markup and behavior**

Add a stable 40x40 icon-only theme button near the login panel top edge. Replace the visible `Show` text with a `visibility` Material Symbol while preserving `#toggle-password`, `aria-controls`, `aria-pressed`, and dynamic title/label changes between “Show password” and “Hide password”. Initialize the admin theme before `requireGuest()` and `checkBackend()`.

- [ ] **Step 4: Apply the compact DICT login CSS**

Keep the desktop identity/form split, simplify the brand treatment, use semantic surface tokens in dark mode, and use a single-column mobile layout below `820px`. Ensure the form stays at a readable maximum width and the theme button does not overlap branding or fields.

- [ ] **Step 5: Verify login tests and static checks**

Run:

```powershell
python -m unittest frontend.tests.test_ui_ux_regressions -v
python frontend\scripts\smoke_check.py
node --check frontend\js\login.js
```

Expected: all checks pass.

---

### Task 3: Public Attendance Document Workflow

**Files:**
- Modify: `frontend/tests/test_ui_ux_regressions.py`
- Modify: `frontend/attendance.html`
- Modify: `frontend/js/attendance.js`
- Modify: `frontend/css/attendance.css`

**Interfaces:**
- Consumes: `initializeThemeToggle(themeToggle, THEME_STORAGE_KEYS.public)` from Task 1.
- Preserves: public event fetch, field visibility/requirements, PSGC cascade, signature drawing/upload, consent dialog, validation, and multipart submission.

- [ ] **Step 1: Write failing public-page regressions**

Assert that `attendance.html` has `color-scheme="light dark"`, `#attendance-theme-toggle`, and accessible header structure. Assert that `attendance.js` initializes `THEME_STORAGE_KEYS.public`. Assert mobile one-column and dark-surface safeguards in `attendance.css`.

- [ ] **Step 2: Run the attendance-specific test and verify RED**

Run: `python -m unittest frontend.tests.test_ui_ux_regressions.UiUxRegressionTests.test_public_attendance_has_an_isolated_accessible_theme_toggle -v`

Expected: FAIL because the public theme control is missing.

- [ ] **Step 3: Update the public header and theme initialization**

Add a right-aligned 40x40 theme button while preserving DICT and optional program logos. Import the shared controller and initialize it with `THEME_STORAGE_KEYS.public` before the event request begins.

- [ ] **Step 4: Refine generated attendance markup presentation hooks**

Add only semantic wrapper classes needed for styling event identity, privacy notice, sections, signature selector, submit region, consent dialog, and success/error states. Do not rename IDs or change text, validation, field visibility, or submission logic.

- [ ] **Step 5: Apply document-style responsive CSS**

Use a constrained readable width, full-width unframed sections separated by lines, compact field spacing, visible consent grouping, clear signature method states, and semantic dark surfaces. At `640px`, switch all fields and dialog actions to one column and keep signature controls stable without clipping.

- [ ] **Step 6: Verify public-page tests and syntax**

Run:

```powershell
python -m unittest frontend.tests.test_ui_ux_regressions -v
python frontend\scripts\smoke_check.py
node --check frontend\js\attendance.js
```

Expected: all checks pass.

---

### Task 4: Browser and Regression Verification

**Files:**
- Temporary audit runner under `.superpowers/verify/`; delete it after verification.
- No production file should change unless the audit reproduces a confirmed issue and a failing regression test is added first.

**Interfaces:**
- Consumes: completed login and attendance pages from Tasks 2 and 3.
- Produces: desktop/mobile light/dark screenshots and measured overflow/console results.

- [ ] **Step 1: Run the complete automated suite**

Run:

```powershell
python -m unittest frontend.tests.test_ui_ux_regressions -v
python frontend\scripts\smoke_check.py
node --check frontend\js\theme.js
node --check frontend\js\login.js
node --check frontend\js\attendance.js
node --check frontend\js\admin.js
```

Expected: every command exits `0`.

- [ ] **Step 2: Audit login states in Chrome**

At desktop `1440x900` and mobile `390x844`, verify light/dark themes, empty form, validation errors, expired-session notice, backend online/offline status, password visibility, focus order, and no page overflow.

- [ ] **Step 3: Audit attendance states in Chrome with read-only fixtures**

Verify loading, incomplete link, unavailable event, full form with all fields, hidden signature, consent dialog, validation errors, submitting, and success. Check desktop/mobile light/dark, canvas visibility, program-logo sizing, no clipped controls, no page overflow, and no console errors.

- [ ] **Step 4: Confirm theme isolation**

Set admin/login to dark and public attendance to light in the same browser origin. Reload both pages and confirm each keeps its own choice. Repeat with reversed values.

- [ ] **Step 5: Remove the temporary audit runner and run the final suite again**

Expected: automated checks remain green after cleanup. Record any untested environmental limitation explicitly in the completion summary.
