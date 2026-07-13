from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.auth import require_super_admin
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app


class FakeSession:
    def __init__(self, records):
        self.records = records

    def scalars(self, statement):
        return SimpleNamespace(all=lambda: self.records)


def make_settings() -> Settings:
    return Settings(jwt_secret_key="test-secret-key-with-more-than-32-bytes")


def make_client(records) -> TestClient:
    app = create_app(make_settings())
    fake_session = FakeSession(records)

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
