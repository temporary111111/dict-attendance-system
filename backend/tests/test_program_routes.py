from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app


class FakeSession:
    def __init__(
        self,
        *,
        listed_programs=None,
        programs=None,
        org_units=None,
        duplicate_program_id=None,
        assignment_visibility_id=None,
        open_event_id=None,
    ):
        self.listed_programs = listed_programs or []
        self.programs = programs or {}
        self.org_units = org_units or {}
        self.duplicate_program_id = duplicate_program_id
        self.assignment_visibility_id = assignment_visibility_id
        self.open_event_id = open_event_id
        self.scalar_statements = []
        self.scalars_statements = []
        self.added_program = None
        self.committed = False

    def scalars(self, statement):
        self.scalars_statements.append(str(statement))
        return SimpleNamespace(all=lambda: self.listed_programs)

    def scalar(self, statement):
        statement_text = str(statement)
        self.scalar_statements.append(statement_text)
        if "program_admin_assignments.assignment_id" in statement_text:
            return self.assignment_visibility_id
        if "events.event_id" in statement_text:
            return self.open_event_id
        return self.duplicate_program_id

    def get(self, model, key):
        if model.__name__ == "Program":
            return self.programs.get(key)
        if model.__name__ == "OrganizationalUnit":
            return self.org_units.get(key)
        return None

    def add(self, program):
        self.added_program = program

    def commit(self):
        self.committed = True

    def rollback(self):
        self.committed = False

    def refresh(self, program):
        if getattr(program, "program_id", None) is None:
            program.program_id = 7


def make_settings() -> Settings:
    return Settings(jwt_secret_key="test-secret-key-with-more-than-32-bytes")


def make_user(role_name="super_admin", user_id=1):
    return SimpleNamespace(
        user_id=user_id,
        role=SimpleNamespace(role_name=role_name, is_active=True),
        account_status="active",
    )


def make_org_unit(org_unit_id=1, *, is_active=True):
    return SimpleNamespace(
        org_unit_id=org_unit_id,
        unit_name="DICT Central Office",
        is_active=is_active,
    )


def make_program(
    program_id=3,
    *,
    owning_unit=None,
    program_name="Free Wi-Fi for All",
    description="Public internet connectivity program.",
    program_status="active",
):
    unit = owning_unit or make_org_unit()
    return SimpleNamespace(
        program_id=program_id,
        owning_unit_id=unit.org_unit_id,
        created_by_user_id=1,
        program_name=program_name,
        description=description,
        logo_path=None,
        program_status=program_status,
        owning_unit=unit,
    )


def make_client(session, *, current_user=None) -> TestClient:
    app = create_app(make_settings())

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return TestClient(app)


def valid_program_payload() -> dict:
    return {
        "owning_unit_id": 1,
        "program_name": "  Free Wi-Fi for All  ",
        "description": "  Public internet connectivity program.  ",
    }


def test_list_programs_returns_all_programs_for_super_admin():
    program = make_program()
    session = FakeSession(listed_programs=[program])
    client = make_client(session, current_user=make_user())

    response = client.get("/api/programs")

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "program_id": 3,
                "owning_unit": {
                    "org_unit_id": 1,
                    "unit_name": "DICT Central Office",
                },
                "created_by_user_id": 1,
                "program_name": "Free Wi-Fi for All",
                "description": "Public internet connectivity program.",
                "logo_url": None,
                "program_status": "active",
            }
        ],
        "message": "Programs retrieved.",
    }


def test_list_programs_filters_by_active_assignment_for_program_admin():
    session = FakeSession(listed_programs=[make_program()])
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.get("/api/programs")

    assert response.status_code == 200
    assert "program_admin_assignments" in session.scalars_statements[0]
    assert "assignment_status" in session.scalars_statements[0]


def test_create_program_normalizes_and_saves_active_program():
    unit = make_org_unit()
    session = FakeSession(org_units={1: unit})
    client = make_client(session, current_user=make_user())

    response = client.post("/api/programs", json=valid_program_payload())

    assert response.status_code == 201
    assert response.json()["data"] == {
        "program_id": 7,
        "owning_unit": {
            "org_unit_id": 1,
            "unit_name": "DICT Central Office",
        },
        "created_by_user_id": 1,
        "program_name": "Free Wi-Fi for All",
        "description": "Public internet connectivity program.",
        "logo_url": None,
        "program_status": "active",
    }
    assert session.added_program.created_by_user_id == 1
    assert session.committed is True


def test_create_program_rejects_duplicate_name_in_same_unit():
    session = FakeSession(
        org_units={1: make_org_unit()},
        duplicate_program_id=8,
    )
    client = make_client(session, current_user=make_user())

    response = client.post("/api/programs", json=valid_program_payload())

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROGRAM_NAME_ALREADY_EXISTS"
    assert session.added_program is None


def test_create_program_rejects_inactive_owning_unit():
    session = FakeSession(org_units={1: make_org_unit(is_active=False)})
    client = make_client(session, current_user=make_user())

    response = client.post("/api/programs", json=valid_program_payload())

    assert response.status_code == 422
    assert "owning_unit_id" in response.json()["error"]["fields"]


def test_get_program_allows_assigned_program_admin():
    program = make_program()
    session = FakeSession(
        programs={3: program},
        assignment_visibility_id=10,
    )
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.get("/api/programs/3")

    assert response.status_code == 200
    assert response.json()["data"]["program_id"] == 3


def test_get_program_rejects_unassigned_program_admin():
    session = FakeSession(programs={3: make_program()})
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.get("/api/programs/3")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_get_program_returns_not_found_for_unknown_id():
    client = make_client(FakeSession(), current_user=make_user())

    response = client.get("/api/programs/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROGRAM_NOT_FOUND"


def test_update_program_changes_fields_and_can_clear_description():
    old_unit = make_org_unit()
    new_unit = make_org_unit(2)
    new_unit.unit_name = "DICT Regional Office"
    program = make_program(owning_unit=old_unit)
    session = FakeSession(
        programs={3: program},
        org_units={2: new_unit},
    )
    client = make_client(session, current_user=make_user())

    response = client.patch(
        "/api/programs/3",
        json={
            "owning_unit_id": 2,
            "program_name": "  eGov Super App  ",
            "description": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["program_name"] == "eGov Super App"
    assert response.json()["data"]["description"] is None
    assert response.json()["data"]["owning_unit"]["org_unit_id"] == 2
    assert session.committed is True


def test_update_program_rejects_empty_payload():
    session = FakeSession(programs={3: make_program()})
    client = make_client(session, current_user=make_user())

    response = client.patch("/api/programs/3", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_archive_and_restore_program_status():
    program = make_program()
    session = FakeSession(
        programs={3: program},
        org_units={1: program.owning_unit},
    )
    client = make_client(session, current_user=make_user())

    archive_response = client.patch(
        "/api/programs/3/archive",
        json={"program_status": "archived"},
    )
    restore_response = client.patch(
        "/api/programs/3/archive",
        json={"program_status": "active"},
    )

    assert archive_response.status_code == 200
    assert archive_response.json()["data"]["program_status"] == "archived"
    assert restore_response.status_code == 200
    assert restore_response.json()["data"]["program_status"] == "active"


def test_restore_program_rejects_inactive_owning_unit():
    unit = make_org_unit(is_active=False)
    program = make_program(owning_unit=unit, program_status="archived")
    session = FakeSession(programs={3: program}, org_units={1: unit})
    client = make_client(session, current_user=make_user())

    response = client.patch(
        "/api/programs/3/archive",
        json={"program_status": "active"},
    )

    assert response.status_code == 422
    assert "owning_unit_id" in response.json()["error"]["fields"]


def test_archive_program_rejects_open_event():
    program = make_program()
    session = FakeSession(
        programs={3: program},
        open_event_id=5,
    )
    client = make_client(session, current_user=make_user())

    response = client.patch(
        "/api/programs/3/archive",
        json={"program_status": "archived"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROGRAM_HAS_OPEN_EVENTS"


def test_program_write_requires_super_admin():
    session = FakeSession(org_units={1: make_org_unit()})
    client = make_client(
        session,
        current_user=make_user("program_admin", user_id=2),
    )

    response = client.post("/api/programs", json=valid_program_payload())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_program_routes_require_authentication():
    client = make_client(FakeSession())

    response = client.get("/api/programs")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
