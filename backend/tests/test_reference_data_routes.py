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
        units_by_id=None,
        active_child_id=None,
    ):
        self.records = records or []
        self.existing_unit_id = existing_unit_id
        self.parent_unit = parent_unit
        self.units_by_id = dict(units_by_id or {})
        if parent_unit is not None:
            self.units_by_id[parent_unit.org_unit_id] = parent_unit
        self.active_child_id = active_child_id
        self.added_unit = None
        self.committed = False

    def scalars(self, statement):
        return SimpleNamespace(all=lambda: self.records)

    def scalar(self, statement):
        statement_text = str(statement)
        if (
            "organizational_units.parent_unit_id" in statement_text
            and "organizational_units.is_active" in statement_text
        ):
            return self.active_child_id
        return self.existing_unit_id

    def get(self, model, key):
        return self.units_by_id.get(key)

    def add(self, unit):
        self.added_unit = unit

    def commit(self):
        self.committed = True

    def rollback(self):
        self.committed = False

    def refresh(self, unit):
        if unit.org_unit_id is None:
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


def make_unit(
    org_unit_id=4,
    *,
    parent_unit_id=1,
    unit_name="Old Unit Name",
    unit_type="office",
    unit_code="OLD",
    is_active=True,
):
    return SimpleNamespace(
        org_unit_id=org_unit_id,
        parent_unit_id=parent_unit_id,
        unit_name=unit_name,
        unit_type=unit_type,
        unit_code=unit_code,
        is_active=is_active,
    )


def test_update_organizational_unit_normalizes_fields_and_reparents():
    target = make_unit()
    root = make_unit(
        1,
        parent_unit_id=None,
        unit_name="DICT",
        unit_type="department",
        unit_code="DICT",
    )
    new_parent = make_unit(
        2,
        parent_unit_id=1,
        unit_name="Regional Office",
        unit_code="RO",
    )
    session = FakeSession(units_by_id={1: root, 2: new_parent, 4: target})
    client = make_client(session=session)

    response = client.patch(
        "/api/organizational-units/4",
        json={
            "unit_name": "  Regional Operations Division  ",
            "unit_type": "  Division  ",
            "unit_code": "  rod  ",
            "parent_unit_id": 2,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "org_unit_id": 4,
            "parent_unit_id": 2,
            "unit_name": "Regional Operations Division",
            "unit_type": "division",
            "unit_code": "ROD",
            "is_active": True,
        },
        "message": "Organizational unit updated.",
    }
    assert session.committed is True


def test_update_organizational_unit_can_clear_code_and_parent():
    target = make_unit()
    session = FakeSession(units_by_id={4: target})
    client = make_client(session=session)

    response = client.patch(
        "/api/organizational-units/4",
        json={"unit_code": None, "parent_unit_id": None},
    )

    assert response.status_code == 200
    assert response.json()["data"]["unit_code"] is None
    assert response.json()["data"]["parent_unit_id"] is None


def test_update_organizational_unit_rejects_unknown_target():
    client = make_client(session=FakeSession())

    response = client.patch(
        "/api/organizational-units/999",
        json={"unit_name": "Unknown"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ORGANIZATIONAL_UNIT_NOT_FOUND"


def test_update_organizational_unit_rejects_duplicate_code():
    target = make_unit()
    session = FakeSession(existing_unit_id=8, units_by_id={4: target})
    client = make_client(session=session)

    response = client.patch(
        "/api/organizational-units/4",
        json={"unit_code": "used"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "UNIT_CODE_ALREADY_EXISTS"


def test_update_organizational_unit_rejects_circular_parent():
    target = make_unit()
    descendant = make_unit(5, parent_unit_id=4, unit_name="Child")
    session = FakeSession(units_by_id={4: target, 5: descendant})
    client = make_client(session=session)

    response = client.patch(
        "/api/organizational-units/4",
        json={"parent_unit_id": 5},
    )

    assert response.status_code == 422
    assert "parent_unit_id" in response.json()["error"]["fields"]


def test_update_organizational_unit_rejects_deactivation_with_active_child():
    target = make_unit()
    session = FakeSession(active_child_id=5, units_by_id={4: target})
    client = make_client(session=session)

    response = client.patch(
        "/api/organizational-units/4",
        json={"is_active": False},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "UNIT_HAS_ACTIVE_CHILDREN"


def test_update_organizational_unit_deactivates_unit_without_active_child():
    target = make_unit()
    session = FakeSession(units_by_id={4: target})
    client = make_client(session=session)

    response = client.patch(
        "/api/organizational-units/4",
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["data"]["is_active"] is False
    assert target.is_active is False


def test_update_organizational_unit_rejects_empty_payload():
    target = make_unit()
    client = make_client(session=FakeSession(units_by_id={4: target}))

    response = client.patch("/api/organizational-units/4", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_update_organizational_unit_requires_authentication():
    client = TestClient(create_app(make_settings()))

    response = client.patch(
        "/api/organizational-units/4",
        json={"unit_name": "Updated Unit"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
