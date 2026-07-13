# FastAPI Stack Decision

## Program and Event Attendance Monitoring and Reporting System for DICT

This document records the selected backend stack and the frontend-backend architecture decision.

## Decision

The project will use Python FastAPI for the backend.

The backend will be designed as an API-only service. It will not assume that frontend files are stored inside the FastAPI project.

## Selected Stack

| Layer | Selected Tool | Purpose |
| --- | --- | --- |
| Backend framework | FastAPI | REST API backend |
| Language | Python 3.11.x | Stable Python version for FastAPI dependencies |
| Server | Uvicorn | Local development and ASGI serving |
| Database | MySQL 8.0+ | Required project database |
| ORM | SQLAlchemy 2.0 | Python models and database queries |
| MySQL driver | PyMySQL | MySQL connection from Python |
| Migration tool | Alembic | Database migration management |
| Validation | Pydantic | Request and response validation |
| Frontend | Vanilla HTML, CSS, JavaScript | Simple frontend that calls the API |

## Frontend-Backend Architecture

The frontend and backend should be treated as separate parts of the system:

```text
frontend/
  public-attendance/
  admin/

backend/
  app/
    main.py
    routers/
    models/
    schemas/
    services/
```

The frontend will call the backend through an API base URL such as:

```text
http://localhost:8000/api
```

In local development, the frontend may run from a simple static server while FastAPI runs through Uvicorn.

In deployment, the frontend and backend may be hosted:

* on the same server,
* on different servers,
* on different subdomains, or
* with the frontend on static hosting and the backend on an API server.

The API design should continue to work in all of these cases.

## CORS Requirement

Because the frontend may be hosted separately, the backend must support configurable CORS origins.

Example development origins:

```text
http://localhost:3000
http://localhost:5173
http://127.0.0.1:5500
```

The final implementation should read allowed origins from environment configuration instead of hardcoding one frontend URL.

## Why This Is the Right Fit

FastAPI is a practical fit because:

* it uses Python, which matches the current backend skill set;
* it has automatic API documentation through `/docs`;
* it works well with MySQL through SQLAlchemy;
* it keeps the backend independent from frontend hosting decisions;
* it avoids adding Node.js as a required backend skill for this project.

## Current Decisions Added During Implementation

* Admin authentication uses stateless JWT Bearer access tokens.
* Uploaded signature images use configurable private local storage.
* QR code images use configurable public local storage.
* The frontend remains separately hostable and calls the backend through its
  configurable API base URL.

## Remaining Non-Decisions

* Which PDF or spreadsheet library will generate the official attendance sheet.
* Where generated attendance-sheet exports will be stored.
* Whether the first frontend version will run from a static server or a simple deployed static host.
