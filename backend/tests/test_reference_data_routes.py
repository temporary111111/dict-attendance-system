from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.auth import require_super_admin
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app


class FakeSession:
    def __init__(
        self,
        records=None,
        *,
        existing_unit_id=None,
        parent_unit=None,
    ):
        self.records = records or []
        self.existing_unit_id = existing_unit_id
        self.parent_unit = parent_unit
        self.added_unit = None
        self.committed = False

    def scalars(self, statement):
        return SimpleNamespace(all=lambda: self.records)

    def scalar(self, statement):
        return self.existing_unit_id

    def get(self, model, key):
        if self.parent_unit and self.parent_unit.org_unit_id == key:
            return self.parent_unit
        return None

    def add(self, unit):
        self.added_unit = unit

    def commit(self):
        self.committed = True

    def rollback(self):
        self.committed = False

    def refresh(self, unit):
        unit.org_unit_id = 4


def make_settings() -> Settings:
    return Settings(jwt_secret_key="test-secret-key-with-more-than-32-bytes")


def make_client(records=None, *, session=None) -> TestClient:
    app = create_app(make_settings())
    fake_session = session or FakeSession(records)

    def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_super_admin] = lambda: SimpleNamespace(user_id=1)
    return TestClient(app)


def test_list_roles_returns_active_role_fields():
    client = make_client(
        [
            SimpleNamespace(
                role_id=2,
                role_name="program_admin",
                description="Manages assigned programs.",
            ),
            SimpleNamespace(
                role_id=1,
                role_name="super_admin",
                description="Manages the whole system.",
            ),
        ]
    )

    response = client.get("/api/roles")

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "role_id": 2,
                "role_name": "program_admin",
                "description": "Manages assigned programs.",
            },
            {
                "role_id": 1,
                "role_name": "super_admin",
                "description": "Manages the whole system.",
            },
        ],
        "message": "Roles retrieved.",
    }


def test_list_organizational_units_returns_hierarchy_fields():
    client = make_client(
        [
            SimpleNamespace(
                org_unit_id=1,
                parent_unit_id=None,
                unit_name="DICT",
                unit_type="department",
                unit_code="DICT",
            ),
            SimpleNamespace(
                org_unit_id=2,
                parent_unit_id=1,
                unit_name="Regional Operations",
                unit_type="office",
                unit_code="RO",
            ),
        ]
    )

    response = client.get("/api/organizational-units")

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "org_unit_id": 1,
                "parent_unit_id": None,
                "unit_name": "DICT",
                "unit_type": "department",
                "unit_code": "DICT",
            },
            {
                "org_unit_id": 2,
                "parent_unit_id": 1,
                "unit_name": "Regional Operations",
                "unit_type": "office",
                "unit_code": "RO",
            },
        ],
        "message": "Organizational units retrieved.",
    }


@pytest.mark.parametrize("path", ["/api/roles", "/api/organizational-units"])
def test_reference_data_routes_require_authentication(path):
    client = TestClient(create_app(make_settings()))

    response = client.get(path)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def make_parent_unit(*, is_active=True):
    return SimpleNamespace(
        org_unit_id=1,
        unit_name="Department of Information and Communications Technology",
        is_active=is_active,
    )


def valid_unit_payload() -> dict:
    return {
        "unit_name": "  Regional Operations Office  ",
        "unit_type": "  Regional Office  ",
        "unit_code": "  ro-ops  ",
        "parent_unit_id": 1,
    }


def test_create_organizational_unit_normalizes_and_saves_active_child():
    session = FakeSession(parent_unit=make_parent_unit())
    client = make_client(session=session)

    response = client.post("/api/organizational-units", json=valid_unit_payload())

    assert response.status_code == 201
    assert response.json() == {
        "data": {
            "org_unit_id": 4,
            "parent_unit_id": 1,
            "unit_name": "Regional Operations Office",
            "unit_type": "regional office",
            "unit_code": "RO-OPS",
        },
        "message": "Organizational unit created.",
    }
    assert session.added_unit.is_active is True
    assert session.committed is True


def test_create_organizational_unit_rejects_duplicate_code():
    session = FakeSession(
        existing_unit_id=8,
        parent_unit=make_parent_unit(),
    )
    client = make_client(session=session)

    response = client.post("/api/organizational-units", json=valid_unit_payload())

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "UNIT_CODE_ALREADY_EXISTS"
    assert session.added_unit is None


def test_create_organizational_unit_rejects_unknown_or_inactive_parent():
    session = FakeSession(parent_unit=None)
    client = make_client(session=session)

    response = client.post("/api/organizational-units", json=valid_unit_payload())

    assert response.status_code == 422
    assert "parent_unit_id" in response.json()["error"]["fields"]


def test_create_organizational_unit_returns_standard_validation_errors():
    client = make_client(session=FakeSession())

    response = client.post(
        "/api/organizational-units",
        json={"unit_name": "", "unit_type": ""},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert set(response.json()["error"]["fields"]) == {"unit_name", "unit_type"}


def test_create_organizational_unit_requires_authentication():
    client = TestClient(create_app(make_settings()))

    response = client.post("/api/organizational-units", json=valid_unit_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
