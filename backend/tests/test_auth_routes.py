from types import SimpleNamespace

from fastapi import Depends
from fastapi.testclient import TestClient

from app.api.dependencies.auth import require_super_admin
from app.core.config import Settings, get_settings
from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.main import create_app


class FakeResult:
    def __init__(self, user):
        self.user = user

    def scalar_one_or_none(self):
        return self.user


class FakeSession:
    def __init__(self, user):
        self.user = user

    def execute(self, statement):
        return FakeResult(self.user)

    def get(self, model, key):
        if self.user and int(key) == self.user.user_id:
            return self.user
        return None


def make_user(role_name: str = "program_admin", account_status: str = "active"):
    return SimpleNamespace(
        user_id=1,
        full_name="Admin User",
        email="admin@example.test",
        password_hash=hash_password("correct-password"),
        account_status=account_status,
        role=SimpleNamespace(role_id=2, role_name=role_name, is_active=True),
        org_unit=SimpleNamespace(org_unit_id=1, unit_name="DICT"),
    )


def make_test_app(user, settings: Settings):
    app = create_app(settings)
    fake_session = FakeSession(user)

    def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: settings
    return app


def make_settings() -> Settings:
    return Settings(
        jwt_secret_key="test-secret-key-with-more-than-32-bytes",
        jwt_access_token_expire_minutes=480,
    )


def test_openapi_uses_http_bearer_for_protected_routes():
    app = create_app(make_settings())

    schema = app.openapi()

    assert schema["components"]["securitySchemes"] == {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
        }
    }
    assert schema["paths"]["/api/auth/me"]["get"]["security"] == [
        {"HTTPBearer": []}
    ]


def test_login_returns_access_token_for_valid_admin():
    settings = make_settings()
    app = make_test_app(make_user(), settings)
    client = TestClient(app)

    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.test", "password": "correct-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Login successful."
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["expires_in_minutes"] == 480
    assert body["data"]["access_token"]


def test_login_rejects_invalid_credentials_with_generic_message():
    settings = make_settings()
    app = make_test_app(make_user(), settings)
    client = TestClient(app)

    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.test", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "INVALID_CREDENTIALS",
            "message": "Invalid email or password.",
            "fields": {},
        }
    }


def test_me_returns_current_user_from_bearer_token():
    settings = make_settings()
    user = make_user()
    app = make_test_app(user, settings)
    client = TestClient(app)
    token = create_access_token(str(user.user_id), settings)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "user_id": 1,
        "full_name": "Admin User",
        "email": "admin@example.test",
        "account_status": "active",
        "role": {
            "role_id": 2,
            "role_name": "program_admin",
        },
        "org_unit": {
            "org_unit_id": 1,
            "unit_name": "DICT",
        },
    }


def test_me_rejects_missing_token():
    settings = make_settings()
    app = make_test_app(make_user(), settings)
    client = TestClient(app)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_logout_returns_success_when_token_is_valid():
    settings = make_settings()
    user = make_user()
    app = make_test_app(user, settings)
    client = TestClient(app)
    token = create_access_token(str(user.user_id), settings)

    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {"logged_out": True},
        "message": "Logout successful. Remove the token on the frontend.",
    }


def test_super_admin_guard_rejects_program_admin():
    settings = make_settings()
    app = make_test_app(make_user(role_name="program_admin"), settings)

    @app.get("/protected-super")
    def protected_super(current_user=Depends(require_super_admin)):
        return {"user_id": current_user.user_id}

    client = TestClient(app)
    token = create_access_token("1", settings)

    response = client.get(
        "/protected-super",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
