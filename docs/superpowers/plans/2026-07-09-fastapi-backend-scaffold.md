# FastAPI Backend Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a runnable API-only FastAPI backend scaffold for the DICT attendance system with health checks, environment config, CORS, and SQLAlchemy MySQL session setup.

**Architecture:** The backend lives in `backend/app` and exposes JSON APIs under `/api`. Frontend files remain outside the FastAPI app, so CORS is configured from environment settings. Database access is centralized in `backend/app/db/session.py` and uses SQLAlchemy with a MySQL URL.

**Tech Stack:** Python 3.11.x, FastAPI, Uvicorn, SQLAlchemy 2.0, PyMySQL, Pydantic Settings, Pytest, HTTPX.

## Global Constraints

* Use Python 3.11.x through the `python` command because local `python --version` is `Python 3.11.9`.
* Keep FastAPI as an API-only backend.
* Do not store frontend files inside the FastAPI backend scaffold.
* Use MySQL 8.0+ as the target database.
* Use SQLAlchemy 2.0 style setup.
* Use PyMySQL for the MySQL driver.
* CORS origins must be configurable through environment settings.
* Keep all API routes under `/api`.
* Use the standard success shape: `{ "data": ..., "message": "..." }`.
* Use the standard error shape: `{ "error": { "code": "...", "message": "...", "fields": {} } }`.
* Do not add Google Forms integration.
* Do not add a dynamic form builder.

---

## File Structure

Create this initial backend structure:

```text
backend/
  .env.example
  README.md
  pytest.ini
  requirements.txt
  app/
    __init__.py
    main.py
    api/
      __init__.py
      health.py
      router.py
    core/
      __init__.py
      config.py
      cors.py
      responses.py
    db/
      __init__.py
      session.py
  tests/
    test_config.py
    test_cors.py
    test_database_session.py
    test_health.py
```

Responsibilities:

* `backend/app/main.py`: creates and exports the FastAPI app.
* `backend/app/api/router.py`: combines API routers under one router.
* `backend/app/api/health.py`: health check endpoints.
* `backend/app/core/config.py`: environment settings.
* `backend/app/core/cors.py`: CORS middleware setup.
* `backend/app/core/responses.py`: shared JSON response helpers.
* `backend/app/db/session.py`: SQLAlchemy engine, session factory, and DB dependency.
* `backend/tests/`: unit tests for the scaffold.

---

### Task 1: Create FastAPI App and Health Endpoint

**Files:**
* Create: `backend/requirements.txt`
* Create: `backend/pytest.ini`
* Create: `backend/app/__init__.py`
* Create: `backend/app/api/__init__.py`
* Create: `backend/app/api/health.py`
* Create: `backend/app/api/router.py`
* Create: `backend/app/core/__init__.py`
* Create: `backend/app/core/responses.py`
* Create: `backend/app/main.py`
* Create: `backend/tests/test_health.py`

**Interfaces:**
* Consumes: none.
* Produces: `app.main.app: FastAPI`
* Produces: `app.main.create_app() -> FastAPI`
* Produces: `app.core.responses.success_response(data: Any, message: str) -> dict[str, Any]`
* Produces: `GET /api/health`

- [ ] **Step 1: Create the failing health endpoint test**

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_success_response():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "data": {"status": "ok"},
        "message": "API is running.",
    }
```

- [ ] **Step 2: Run the health test and confirm it fails**

Run from `backend`:

```powershell
python -m pytest tests/test_health.py -v
```

Expected result:

```text
ModuleNotFoundError: No module named 'app'
```

- [ ] **Step 3: Add dependencies and pytest config**

Create `backend/requirements.txt`:

```text
fastapi>=0.110,<1.0
uvicorn[standard]>=0.27,<1.0
sqlalchemy>=2.0,<3.0
pymysql>=1.1,<2.0
pydantic-settings>=2.2,<3.0
python-dotenv>=1.0,<2.0
alembic>=1.13,<2.0
pytest>=8.0,<9.0
httpx>=0.27,<1.0
```

Create `backend/pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 4: Add the minimal app package**

Create empty package marker files:

```text
backend/app/__init__.py
backend/app/api/__init__.py
backend/app/core/__init__.py
```

Create `backend/app/core/responses.py`:

```python
from typing import Any


def success_response(data: Any, message: str) -> dict[str, Any]:
    return {
        "data": data,
        "message": message,
    }
```

Create `backend/app/api/health.py`:

```python
from typing import Any

from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def read_health() -> dict[str, Any]:
    return success_response({"status": "ok"}, "API is running.")
```

Create `backend/app/api/router.py`:

```python
from fastapi import APIRouter

from app.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
```

Create `backend/app/main.py`:

```python
from fastapi import FastAPI

from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="DICT Attendance System API",
        version="0.1.0",
    )
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
```

- [ ] **Step 5: Install dependencies and run the health test**

Run from `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests/test_health.py -v
```

Expected result:

```text
1 passed
```

- [ ] **Step 6: Commit Task 1**

```powershell
git add backend/requirements.txt backend/pytest.ini backend/app backend/tests/test_health.py
git commit -m "feat: scaffold fastapi health endpoint"
```

---

### Task 2: Add Environment Settings and Configurable CORS

**Files:**
* Create: `backend/.env.example`
* Create: `backend/app/core/config.py`
* Create: `backend/app/core/cors.py`
* Create: `backend/tests/test_config.py`
* Create: `backend/tests/test_cors.py`
* Modify: `backend/app/main.py`

**Interfaces:**
* Consumes: `app.main.create_app() -> FastAPI`
* Produces: `app.core.config.Settings`
* Produces: `app.core.config.get_settings() -> Settings`
* Produces: `app.core.cors.configure_cors(app: FastAPI, settings: Settings) -> None`
* Produces: `app.main.create_app(settings: Settings | None = None) -> FastAPI`

- [ ] **Step 1: Create failing settings and CORS tests**

Create `backend/tests/test_config.py`:

```python
from app.core.config import Settings


def test_settings_parse_comma_separated_cors_origins():
    settings = Settings(
        cors_origins="http://localhost:5500, http://127.0.0.1:5500"
    )

    assert settings.cors_origins == [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]


def test_settings_keep_list_cors_origins():
    settings = Settings(cors_origins=["http://example.test"])

    assert settings.cors_origins == ["http://example.test"]
```

Create `backend/tests/test_cors.py`:

```python
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_configured_origin_is_allowed_by_cors():
    app = create_app(Settings(cors_origins=["http://frontend.test"]))
    client = TestClient(app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://frontend.test",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://frontend.test"
```

- [ ] **Step 2: Run the new tests and confirm they fail**

Run from `backend`:

```powershell
python -m pytest tests/test_config.py tests/test_cors.py -v
```

Expected result:

```text
ModuleNotFoundError: No module named 'app.core.config'
```

- [ ] **Step 3: Add environment example**

Create `backend/.env.example`:

```text
APP_NAME=DICT Attendance System API
APP_VERSION=0.1.0
ENVIRONMENT=development
API_PREFIX=/api
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/dict_attendance_system?charset=utf8mb4
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:5500"]
```

- [ ] **Step 4: Add settings and CORS implementation**

Create `backend/app/core/config.py`:

```python
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DICT Attendance System API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str = (
        "mysql+pymysql://root:password@localhost:3306/"
        "dict_attendance_system?charset=utf8mb4"
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5500",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Create `backend/app/core/cors.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings


def configure_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.cors import configure_cors


def create_app(settings: Settings | None = None) -> FastAPI:
    current_settings = settings or get_settings()
    app = FastAPI(
        title=current_settings.app_name,
        version=current_settings.app_version,
    )
    configure_cors(app, current_settings)
    app.include_router(api_router, prefix=current_settings.api_prefix)
    return app


app = create_app()
```

- [ ] **Step 5: Run settings, CORS, and health tests**

Run from `backend`:

```powershell
python -m pytest tests/test_config.py tests/test_cors.py tests/test_health.py -v
```

Expected result:

```text
4 passed
```

- [ ] **Step 6: Commit Task 2**

```powershell
git add backend/.env.example backend/app/core/config.py backend/app/core/cors.py backend/app/main.py backend/tests/test_config.py backend/tests/test_cors.py
git commit -m "feat: add fastapi settings and cors"
```

---

### Task 3: Add SQLAlchemy Database Session Foundation

**Files:**
* Create: `backend/app/db/__init__.py`
* Create: `backend/app/db/session.py`
* Create: `backend/tests/test_database_session.py`

**Interfaces:**
* Consumes: `app.core.config.get_settings() -> Settings`
* Produces: `app.db.session.create_database_engine(database_url: str) -> sqlalchemy.engine.Engine`
* Produces: `app.db.session.SessionLocal`
* Produces: `app.db.session.get_db() -> Generator[Session, None, None]`

- [ ] **Step 1: Create failing database session tests**

Create `backend/tests/test_database_session.py`:

```python
import pytest
from sqlalchemy.engine import Engine

from app.db.session import create_database_engine, get_db


def test_create_database_engine_uses_given_url():
    engine = create_database_engine("sqlite+pysqlite:///:memory:")

    assert isinstance(engine, Engine)
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


def test_get_db_closes_session(monkeypatch):
    created_sessions = []

    class FakeSession:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    def fake_session_local():
        session = FakeSession()
        created_sessions.append(session)
        return session

    monkeypatch.setattr("app.db.session.SessionLocal", fake_session_local)

    generator = get_db()
    yielded_session = next(generator)

    assert yielded_session is created_sessions[0]

    with pytest.raises(StopIteration):
        next(generator)

    assert created_sessions[0].closed is True
```

- [ ] **Step 2: Run the database session tests and confirm they fail**

Run from `backend`:

```powershell
python -m pytest tests/test_database_session.py -v
```

Expected result:

```text
ModuleNotFoundError: No module named 'app.db'
```

- [ ] **Step 3: Add database session code**

Create empty package marker file:

```text
backend/app/db/__init__.py
```

Create `backend/app/db/session.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_database_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


settings = get_settings()
engine = create_database_engine(settings.database_url)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Run database session tests**

Run from `backend`:

```powershell
python -m pytest tests/test_database_session.py -v
```

Expected result:

```text
2 passed
```

- [ ] **Step 5: Run all scaffold tests**

Run from `backend`:

```powershell
python -m pytest -v
```

Expected result:

```text
6 passed
```

- [ ] **Step 6: Commit Task 3**

```powershell
git add backend/app/db backend/tests/test_database_session.py
git commit -m "feat: add sqlalchemy session foundation"
```

---

### Task 4: Add Database Health Endpoint

**Files:**
* Modify: `backend/app/api/health.py`
* Modify: `backend/app/core/responses.py`
* Modify: `backend/tests/test_health.py`

**Interfaces:**
* Consumes: `app.db.session.get_db() -> Generator[Session, None, None]`
* Consumes: `app.core.responses.success_response(data: Any, message: str) -> dict[str, Any]`
* Produces: `app.core.responses.error_response(code: str, message: str, fields: dict[str, Any] | None = None) -> dict[str, Any]`
* Produces: `GET /api/health/db`

- [ ] **Step 1: Add failing database health tests**

Replace `backend/tests/test_health.py` with:

```python
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.main import app


def test_health_check_returns_success_response():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "data": {"status": "ok"},
        "message": "API is running.",
    }


def test_database_health_returns_success_response():
    class FakeDb:
        def execute(self, statement):
            self.statement = str(statement)

    def override_get_db():
        yield FakeDb()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        response = client.get("/api/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "data": {"database": "ok"},
        "message": "Database connection is available.",
    }


def test_database_health_returns_503_when_query_fails():
    class FailingDb:
        def execute(self, statement):
            raise SQLAlchemyError("database unavailable")

    def override_get_db():
        yield FailingDb()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        response = client.get("/api/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "DATABASE_UNAVAILABLE",
            "message": "Database connection is unavailable.",
            "fields": {},
        }
    }
```

- [ ] **Step 2: Run health tests and confirm the new tests fail**

Run from `backend`:

```powershell
python -m pytest tests/test_health.py -v
```

Expected result:

```text
FAILED tests/test_health.py::test_database_health_returns_success_response
FAILED tests/test_health.py::test_database_health_returns_503_when_query_fails
```

- [ ] **Step 3: Add error response helper**

Replace `backend/app/core/responses.py` with:

```python
from typing import Any


def success_response(data: Any, message: str) -> dict[str, Any]:
    return {
        "data": data,
        "message": message,
    }


def error_response(
    code: str,
    message: str,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "fields": fields or {},
        }
    }
```

- [ ] **Step 4: Add database health endpoint**

Replace `backend/app/api/health.py` with:

```python
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.responses import error_response, success_response
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def read_health() -> dict[str, Any]:
    return success_response({"status": "ok"}, "API is running.")


@router.get("/db")
def read_database_health(db: Session = Depends(get_db)) -> dict[str, Any] | JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content=error_response(
                "DATABASE_UNAVAILABLE",
                "Database connection is unavailable.",
            ),
        )

    return success_response(
        {"database": "ok"},
        "Database connection is available.",
    )
```

- [ ] **Step 5: Run health and all scaffold tests**

Run from `backend`:

```powershell
python -m pytest tests/test_health.py -v
python -m pytest -v
```

Expected result:

```text
3 passed
8 passed
```

- [ ] **Step 6: Commit Task 4**

```powershell
git add backend/app/api/health.py backend/app/core/responses.py backend/tests/test_health.py
git commit -m "feat: add database health check"
```

---

### Task 5: Add Backend README and Manual Run Check

**Files:**
* Create: `backend/README.md`

**Interfaces:**
* Consumes: `backend/.env.example`
* Consumes: `app.main.app: FastAPI`
* Produces: local run instructions for the FastAPI backend.

- [ ] **Step 1: Create backend README**

Create `backend/README.md`:

````markdown
# DICT Attendance System Backend

FastAPI API-only backend for the DICT Program and Event Attendance Monitoring and Reporting System.

## Stack

* Python 3.11.x
* FastAPI
* Uvicorn
* SQLAlchemy 2.0
* PyMySQL
* MySQL 8.0+
* Pytest

## Setup

Run from this `backend` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `DATABASE_URL` to your local MySQL database:

```text
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/dict_attendance_system?charset=utf8mb4
```

## Run

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/health/db
```

## Test

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -v
```

## Frontend Hosting

The frontend is separate from this FastAPI backend. The frontend should call the backend using a configurable API base URL such as:

```text
http://127.0.0.1:8000/api
```

When the frontend runs on a different host or port, add that frontend origin to `CORS_ORIGINS` in `.env`.
````

- [ ] **Step 2: Verify README contains run command**

Run from repo root:

```powershell
Get-Content .\backend\README.md | Select-String -Pattern "uvicorn app.main:app --reload"
```

Expected result:

```text
uvicorn app.main:app --reload
```

- [ ] **Step 3: Run all scaffold tests**

Run from `backend`:

```powershell
python -m pytest -v
```

Expected result:

```text
8 passed
```

- [ ] **Step 4: Commit Task 5**

```powershell
git add backend/README.md
git commit -m "docs: add backend setup guide"
```

---

## Final Verification

Run from `backend`:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -v
uvicorn app.main:app --reload
```

Expected test result:

```text
8 passed
```

Expected manual browser checks:

```text
http://127.0.0.1:8000/docs loads FastAPI documentation.
http://127.0.0.1:8000/api/health returns status ok.
http://127.0.0.1:8000/api/health/db returns database ok when DATABASE_URL points to the local MySQL database.
```

If `/api/health/db` returns `DATABASE_UNAVAILABLE`, check:

* MySQL service is running.
* `dict_attendance_system` database exists.
* `.env` contains the correct MySQL username and password.
* `DATABASE_URL` uses `mysql+pymysql://`.
