# Frontend

Separate vanilla HTML, CSS, at JavaScript client ito para sa FastAPI backend.
Hindi kailangang ilagay o i-serve ng FastAPI ang frontend files.

## Current Admin Views

* Login with stateless JWT access token
* Role-scoped dashboard summary
* Program creation and editing for Super Admin
* Organizational unit and admin-user management for Super Admin
* Program Admin assignment and revocation within each program
* Event creation, editing, QR/link generation, and attendance lifecycle actions
* Per-event fixed attendance field requirements
* Attendance record review and status update for authorized admins
* Generated DICT attendance-sheet PDF download per event
* Program and event attendance summary reports
* Paginated and filtered audit logs for Super Admin only

## Local Run

Start the backend from `backend/`:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Start the frontend from the project root in a separate terminal:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Open:

```text
http://127.0.0.1:5500/
```

## API Configuration

Edit `js/config.js` when the backend host changes:

```javascript
window.APP_CONFIG = Object.freeze({
  apiBaseUrl: "http://127.0.0.1:8000/api",
});
```

The frontend origin must also be allowed in backend `CORS_ORIGINS`.

## Access Token Storage

Default login uses `sessionStorage`, so closing the browser session removes the
token. Checking **Keep me signed in on this device** uses `localStorage` until
the token expires or the admin signs out. The token is sent as a Bearer token
and is not compared with a token stored in MySQL.

## Static Check

Run from the project root:

```powershell
python frontend\scripts\smoke_check.py
```

The checker validates local HTML references, duplicate element IDs, JavaScript
module imports, and the configured API URL without requiring Node.js.
