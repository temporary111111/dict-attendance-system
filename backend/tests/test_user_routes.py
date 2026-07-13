from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies.auth import require_super_admin
from app.core.config import Settings
from app.core.security import verify_password
from app.db.session import get_db
from app.main import create_app


class FakeSession:
    def __init__(
        self,
        *,
        existing_user_id=None,
        role=None,
        org_unit=None,
    ):
        self.existing_user_id = existing_user_id
        self.role = role
        self.org_unit = org_unit
        self.added_user = None
        self.committed = False

    def scalar(self, statement):
        return self.existing_user_id

    def get(self, model, key):
        if model.__name__ == "Role":
            return self.role if self.role and self.role.role_id == key else None
        if model.__name__ == "OrganizationalUnit":
            if self.org_unit and self.org_unit.org_unit_id == key:
                return self.org_unit
        return None

    def add(self, user):
        self.added_user = user

    def commit(self):
        self.committed = True

    def refresh(self, user):
        user.user_id = 3

    def rollback(self):
        self.committed = False


def make_settings() -> Settings:
    return Settings(jwt_secret_key="test-secret-key-with-more-than-32-bytes")


def make_role(*, is_active=True):
    return SimpleNamespace(
        role_id=2,
        role_name="program_admin",
        is_active=is_active,
    )


def make_org_unit(*, is_active=True):
    return SimpleNamespace(
        org_unit_id=1,
        unit_name="DICT Regional Office",
        is_active=is_active,
    )


def make_client(session: FakeSession, *, authorized=True) -> TestClient:
    app = create_app(make_settings())

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    if authorized:
        app.dependency_overrides[require_super_admin] = lambda: SimpleNamespace(
            user_id=1
        )
    return TestClient(app)


def valid_payload() -> dict:
    return {
        "full_name": "  Juan Dela Cruz  ",
        "email": "JUAN.DELA.CRUZ@EXAMPLE.TEST",
        "password": "secure-password",
        "role_id": 2,
        "org_unit_id": 1,
    }


def test_create_user_hashes_password_and_returns_safe_account_data():
    session = FakeSession(role=make_role(), org_unit=make_org_unit())
    client = make_client(session)

    response = client.post("/api/users", json=valid_payload())

    assert response.status_code == 201
    assert response.json() == {
        "data": {
            "user_id": 3,
            "full_name": "Juan Dela Cruz",
            "email": "juan.dela.cruz@example.test",
            "account_status": "active",
            "role": {
                "role_id": 2,
                "role_name": "program_admin",
            },
            "org_unit": {
                "org_unit_id": 1,
                "unit_name": "DICT Regional Office",
            },
        },
        "message": "Admin user created.",
    }
    assert session.committed is True
    assert session.added_user.password_hash != "secure-password"
    assert verify_password(
        "secure-password",
        session.added_user.password_hash,
    )


def test_create_user_rejects_duplicate_email():
    session = FakeSession(
        existing_user_id=9,
        role=make_role(),
        org_unit=make_org_unit(),
    )
    client = make_client(session)

    response = client.post("/api/users", json=valid_payload())

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "EMAIL_ALREADY_EXISTS",
        "message": "An admin user with this email already exists.",
        "fields": {"email": "Email is already in use."},
    }
    assert session.added_user is None


def test_create_user_rejects_unknown_or_inactive_role():
    session = FakeSession(role=None, org_unit=make_org_unit())
    client = make_client(session)

    response = client.post("/api/users", json=valid_payload())

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "role_id" in response.json()["error"]["fields"]


def test_create_user_rejects_unknown_or_inactive_org_unit():
    session = FakeSession(role=make_role(), org_unit=None)
    client = make_client(session)

    response = client.post("/api/users", json=valid_payload())

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "org_unit_id" in response.json()["error"]["fields"]


def test_create_user_returns_standard_field_validation_errors():
    session = FakeSession(role=make_role(), org_unit=make_org_unit())
    client = make_client(session)
    payload = valid_payload()
    payload["email"] = "not-an-email"
    payload["password"] = "short"

    response = client.post("/api/users", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert set(response.json()["error"]["fields"]) == {"email", "password"}


def test_create_user_requires_authentication():
    session = FakeSession(role=make_role(), org_unit=make_org_unit())
    client = make_client(session, authorized=False)

    response = client.post("/api/users", json=valid_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
