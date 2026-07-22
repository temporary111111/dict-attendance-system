# Login Brand Background Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ibalik ang enlarged DICT header background sa desktop login identity panel nang hindi naaapektuhan ang form readability, dark mode, o mobile layout.

**Architecture:** CSS-only ang visual treatment. Gagamitin ng `.login-brand` ang existing `../assets/dict-header.png` bilang background image sa ilalim ng existing blue base color at multiply blend mode. Existing `.brand-image` ang mananatiling white DICT logo card sa ibabaw.

**Tech Stack:** Vanilla CSS, Python `unittest` static regression test, Chrome screenshot verification.

## Global Constraints

- Desktop login branding panel lang ang babaguhin.
- Walang auth, validation, session, theme-key, o mobile behavior change.
- Walang bagong asset o dependency.
- Huwag magpatakbo ng Git commands; user ang may hawak ng version control.

---

### Task 1: Restore the Desktop DICT Header Background

**Files:**
- Modify: `frontend/tests/test_ui_ux_regressions.py`
- Modify: `frontend/css/login.css`

**Interfaces:**
- Consumes: existing `frontend/assets/dict-header.png`.
- Preserves: `.login-brand`, `.brand-image`, desktop branding copy, and the mobile rule that hides `.login-brand` below `820px`.

- [ ] **Step 1: Write the failing regression test**

Add a test asserting that the `.login-brand` CSS block contains all of these visual safeguards:

```python
self.assertIn('background-image: url("../assets/dict-header.png");', login_css)
self.assertIn("background-position: center;", login_css)
self.assertIn("background-size: cover;", login_css)
self.assertIn("background-blend-mode: multiply;", login_css)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m unittest frontend.tests.test_ui_ux_regressions.UiUxRegressionTests.test_login_brand_restores_the_dict_header_background -v`

Expected: FAIL because `login.css` currently has a flat background only.

- [ ] **Step 3: Implement the minimal CSS treatment**

In `.login-brand`, retain the dark DICT blue base and add:

```css
background-image: url("../assets/dict-header.png");
background-position: center;
background-size: cover;
background-blend-mode: multiply;
```

Do not change `@media (max-width: 820px)`, which keeps the brand panel hidden on mobile.

- [ ] **Step 4: Verify automated checks**

Run:

```powershell
python -m unittest frontend.tests.test_ui_ux_regressions -v
python frontend\scripts\smoke_check.py
```

Expected: all checks pass.

- [ ] **Step 5: Verify in Chrome**

At desktop `1440x900`, confirm the enlarged DICT header is visible behind the white logo card and the login title remains readable. At mobile `390x844`, confirm the identity background remains hidden and there is no horizontal overflow.
