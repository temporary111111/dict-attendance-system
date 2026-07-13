from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app

ASSIGNED_AT = datetime(2026, 7, 13, 9, 0, 0)


class FakeSession:
    def __init__(
        self,
        *,
        programs=None,
        users=None,
        assignments=None,
        listed_assignments=None,
        existing_assignment=None,
    ):
        self.programs = programs or {}
        self.users = users or {}
        self.assignments = assignments or {}
        self.listed_assignments = listed_assignments or []
        self.existing_assignment = existing_assignment
        self.added_assignment = None
        self.committed = False

    def get(self, model, key):
        if model.__name__ == "Program":
            return self.programs.get(key)
        if model.__name__ == "User":
            return self.users.get(key)
        if model.__name__ == "ProgramAdminAssignment":
            return self.assignments.get(key)
        return None

    def scalar(self, statement):
        return self.existing_assignment

    def scalars(self, statement):
        return SimpleNamespace(all=lambda: self.listed_assignments)

    def add(self, assignment):
        self.added_assignment = assignment

    def commit(self):
        self.committed = True

    def rollback(self):
        self.committed = False

    def refresh(self, assignment):
        if getattr(assignment, "assignment_id", None) is None:
            assignment.assignment_id = 11
        if getattr(assignment, "assigned_at", None) is None:
            assignment.assigned_at = ASSIGNED_AT


def make_settings() -> Settings:
    return Settings(jwt_secret_key="test-secret-key-with-more-than-32-bytes")


def make_current_user(role_name="super_admin", user_id=1):
    return SimpleNamespace(
        user_id=user_id,
        role=SimpleNamespace(role_name=role_name, is_active=True),
        account_status="active",
    )


def make_program(program_id=3, *, status="active"):
    return SimpleNamespace(
        program_id=program_id,
        program_name="Free Wi-Fi for All",
        program_status=status,
    )


def make_program_admin(user_id=2, *, active=True, role_name="program_admin"):
    return SimpleNamespace(
        user_id=user_id,
        full_name="Juan Dela Cruz",
        email="juan@example.com",
        account_status="active" if active else "inactive",
        role=SimpleNamespace(role_name=role_name, is_active=True),
    )


def make_assignment(
    assignment_id=10,
    *,
    status="active",
    user=None,
    revoked_at=None,
):
    assigned_user = user or make_program_admin()
    return SimpleNamespace(
        assignment_id=assignment_id,
        program_id=3,
        user_id=assigned_user.user_id,
        user=assigned_user,
        assigned_by_user_id=1,
        assignment_status=status,
        assigned_at=ASSIGNED_AT,
        revoked_at=revoked_at,
    )


def make_client(session, *, current_user=None) -> TestClient:
    app = create_app(make_settings())

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return TestClient(app)


def test_list_program_admin_assignments_includes_active_and_revoked_history():
    active = make_assignment()
    revoked = make_assignment(
        9,
        status="revoked",
        revoked_at=datetime(2026, 7, 12, 12, 0, 0),
    )
    session = FakeSession(
        programs={3: make_program()},
        listed_assignments=[active, revoked],
    )
    client = make_client(session, current_user=make_current_user())

    response = client.get("/api/programs/3/admins")

    assert response.status_code == 200
    assert len(response.json()["data"]) == 2
    assert response.json()["data"][0]["assignment_status"] == "active"
    assert response.json()["data"][1]["assignment_status"] == "revoked"


def test_list_program_admin_assignments_returns_program_not_found():
    client = make_client(FakeSession(), current_user=make_current_user())

    response = client.get("/api/programs/999/admins")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROGRAM_NOT_FOUND"


def test_assign_program_admin_creates_active_assignment():
    user = make_program_admin()
    session = FakeSession(
        programs={3: make_program()},
        users={2: user},
    )
    client = make_client(session, current_user=make_current_user())

    response = client.post("/api/programs/3/admins", json={"user_id": 2})

    assert response.status_code == 201
    assert response.json()["data"]["assignment_id"] == 11
    assert response.json()["data"]["user"]["user_id"] == 2
    assert response.json()["data"]["assignment_status"] == "active"
    assert session.added_assignment.assigned_by_user_id == 1
    assert session.committed is True


def test_assign_program_admin_rejects_archived_program():
    session = FakeSession(programs={3: make_program(status="archived")})
    client = make_client(session, current_user=make_current_user())

    response = client.post("/api/programs/3/admins", json={"user_id": 2})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROGRAM_ARCHIVED"


def test_assign_program_admin_rejects_inactive_or_wrong_role_user():
    user = make_program_admin(active=False)
    session = FakeSession(
        programs={3: make_program()},
        users={2: user},
    )
    client = make_client(session, current_user=make_current_user())

    response = client.post("/api/programs/3/admins", json={"user_id": 2})

    assert response.status_code == 422
    assert "user_id" in response.json()["error"]["fields"]


def test_assign_program_admin_rejects_already_active_assignment():
    user = make_program_admin()
    session = FakeSession(
        programs={3: make_program()},
        users={2: user},
        existing_assignment=make_assignment(user=user),
    )
    client = make_client(session, current_user=make_current_user())

    response = client.post("/api/programs/3/admins", json={"user_id": 2})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ASSIGNMENT_ALREADY_ACTIVE"


def test_assign_program_admin_reactivates_revoked_unique_row():
    user = make_program_admin()
    revoked = make_assignment(
        status="revoked",
        user=user,
        revoked_at=datetime(2026, 7, 12, 12, 0, 0),
    )
    session = FakeSession(
        programs={3: make_program()},
        users={2: user},
        existing_assignment=revoked,
    )
    client = make_client(session, current_user=make_current_user(user_id=5))

    response = client.post("/api/programs/3/admins", json={"user_id": 2})

    assert response.status_code == 200
    assert response.json()["data"]["assignment_id"] == 10
    assert response.json()["data"]["assignment_status"] == "active"
    assert revoked.revoked_at is None
    assert revoked.assigned_by_user_id == 5


def test_revoke_program_admin_assignment_sets_status_and_timestamp():
    assignment = make_assignment()
    session = FakeSession(assignments={10: assignment})
    client = make_client(session, current_user=make_current_user())

    response = client.patch("/api/program-admin-assignments/10/revoke")

    assert response.status_code == 200
    assert response.json()["data"]["assignment_status"] == "revoked"
    assert response.json()["data"]["revoked_at"] is not None
    assert assignment.revoked_at is not None
    assert session.committed is True


def test_revoke_program_admin_assignment_is_idempotent():
    revoked_at = datetime(2026, 7, 12, 12, 0, 0)
    assignment = make_assignment(
        status="revoked",
        revoked_at=revoked_at,
    )
    session = FakeSession(assignments={10: assignment})
    client = make_client(session, current_user=make_current_user())

    response = client.patch("/api/program-admin-assignments/10/revoke")

    assert response.status_code == 200
    assert assignment.revoked_at == revoked_at
    assert session.committed is False


def test_revoke_program_admin_assignment_returns_not_found():
    client = make_client(FakeSession(), current_user=make_current_user())

    response = client.patch("/api/program-admin-assignments/999/revoke")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ASSIGNMENT_NOT_FOUND"


def test_assignment_routes_require_super_admin():
    session = FakeSession(programs={3: make_program()})
    client = make_client(
        session,
        current_user=make_current_user("program_admin", user_id=2),
    )

    response = client.get("/api/programs/3/admins")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_assignment_routes_require_authentication():
    client = make_client(FakeSession())

    response = client.get("/api/programs/3/admins")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
