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
        listed_users=None,
        detail_user=None,
        user_to_update=None,
    ):
        self.existing_user_id = existing_user_id
        self.role = role
        self.org_unit = org_unit
        self.listed_users = listed_users or []
        self.detail_user = detail_user
        self.user_to_update = user_to_update
        self.added_user = None
        self.committed = False

    def scalar(self, statement):
        if self.detail_user is not None:
            return self.detail_user
        return self.existing_user_id

    def scalars(self, statement):
        return SimpleNamespace(all=lambda: self.listed_users)

    def get(self, model, key):
        if model.__name__ == "User":
            if self.user_to_update and self.user_to_update.user_id == key:
                return self.user_to_update
            return None
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
        if getattr(user, "user_id", None) is None:
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
        "email": "JUAN.DELA.CRUZ@EXAMPLE.COM",
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
            "email": "juan.dela.cruz@example.com",
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


def test_list_users_returns_safe_active_and_inactive_accounts():
    program_admin_role = make_role()
    super_admin_role = SimpleNamespace(
        role_id=1,
        role_name="super_admin",
        is_active=True,
    )
    org_unit = make_org_unit()
    session = FakeSession(
        listed_users=[
            SimpleNamespace(
                user_id=2,
                full_name="Ana Reyes",
                email="ana.reyes@example.com",
                password_hash="must-not-be-returned",
                account_status="active",
                role=program_admin_role,
                org_unit=org_unit,
            ),
            SimpleNamespace(
                user_id=1,
                full_name="System Admin",
                email="admin@example.com",
                password_hash="must-not-be-returned",
                account_status="inactive",
                role=super_admin_role,
                org_unit=None,
            ),
        ]
    )
    client = make_client(session)

    response = client.get("/api/users")

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "user_id": 2,
                "full_name": "Ana Reyes",
                "email": "ana.reyes@example.com",
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
            {
                "user_id": 1,
                "full_name": "System Admin",
                "email": "admin@example.com",
                "account_status": "inactive",
                "role": {
                    "role_id": 1,
                    "role_name": "super_admin",
                },
                "org_unit": None,
            },
        ],
        "message": "Admin users retrieved.",
    }


def test_list_users_requires_authentication():
    client = make_client(FakeSession(), authorized=False)

    response = client.get("/api/users")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_get_user_returns_safe_account_data():
    user = SimpleNamespace(
        user_id=2,
        full_name="Ana Reyes",
        email="ana.reyes@example.com",
        password_hash="must-not-be-returned",
        account_status="active",
        role=make_role(),
        org_unit=make_org_unit(),
    )
    client = make_client(FakeSession(detail_user=user))

    response = client.get("/api/users/2")

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "user_id": 2,
            "full_name": "Ana Reyes",
            "email": "ana.reyes@example.com",
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
        "message": "Admin user retrieved.",
    }


def test_get_user_returns_not_found_for_unknown_id():
    client = make_client(FakeSession(detail_user=None))

    response = client.get("/api/users/999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "USER_NOT_FOUND",
            "message": "Admin user not found.",
            "fields": {},
        }
    }


def test_get_user_requires_authentication():
    client = make_client(FakeSession(), authorized=False)

    response = client.get("/api/users/2")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def make_existing_user():
    return SimpleNamespace(
        user_id=2,
        role_id=2,
        org_unit_id=1,
        full_name="Ana Reyes",
        email="ana.reyes@example.com",
        password_hash="existing-password-hash",
        account_status="active",
        role=make_role(),
        org_unit=make_org_unit(),
    )


def test_update_user_changes_profile_and_can_clear_org_unit():
    user = make_existing_user()
    new_role = SimpleNamespace(
        role_id=1,
        role_name="super_admin",
        is_active=True,
    )
    session = FakeSession(user_to_update=user, role=new_role)
    client = make_client(session)

    response = client.patch(
        "/api/users/2",
        json={
            "full_name": "  Ana Updated  ",
            "email": "ANA.UPDATED@EXAMPLE.COM",
            "role_id": 1,
            "org_unit_id": None,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "user_id": 2,
            "full_name": "Ana Updated",
            "email": "ana.updated@example.com",
            "account_status": "active",
            "role": {"role_id": 1, "role_name": "super_admin"},
            "org_unit": None,
        },
        "message": "Admin user updated.",
    }
    assert user.password_hash == "existing-password-hash"
    assert session.committed is True


def test_update_user_rejects_duplicate_email():
    session = FakeSession(
        existing_user_id=9,
        user_to_update=make_existing_user(),
    )
    client = make_client(session)

    response = client.patch(
        "/api/users/2",
        json={"email": "existing@example.com"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_update_user_returns_not_found_for_unknown_id():
    client = make_client(FakeSession(user_to_update=None))

    response = client.patch("/api/users/999", json={"full_name": "New Name"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"


def test_update_user_rejects_invalid_role():
    session = FakeSession(user_to_update=make_existing_user(), role=None)
    client = make_client(session)

    response = client.patch("/api/users/2", json={"role_id": 999})

    assert response.status_code == 422
    assert "role_id" in response.json()["error"]["fields"]


def test_update_user_rejects_invalid_org_unit():
    session = FakeSession(user_to_update=make_existing_user(), org_unit=None)
    client = make_client(session)

    response = client.patch("/api/users/2", json={"org_unit_id": 999})

    assert response.status_code == 422
    assert "org_unit_id" in response.json()["error"]["fields"]


def test_update_user_rejects_empty_payload():
    client = make_client(FakeSession(user_to_update=make_existing_user()))

    response = client.patch("/api/users/2", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_update_user_requires_authentication():
    client = make_client(
        FakeSession(user_to_update=make_existing_user()),
        authorized=False,
    )

    response = client.patch("/api/users/2", json={"full_name": "New Name"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
