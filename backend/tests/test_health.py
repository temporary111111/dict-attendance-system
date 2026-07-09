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
