import pytest

from app.core.security import verify_password
from app.models import OrganizationalUnit, Role, User
from scripts.create_admin_user import (
    AdminSetupError,
    create_or_update_super_admin,
)


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeSession:
    def __init__(self, results):
        self.results = list(results)
        self.added = []
        self.committed = False
        self.refreshed = []

    def execute(self, statement):
        return FakeResult(self.results.pop(0))

    def add(self, value):
        self.added.append(value)

    def commit(self):
        self.committed = True

    def refresh(self, value):
        self.refreshed.append(value)


def make_super_admin_role():
    return Role(role_id=1, role_name="super_admin", is_active=True)


def make_dict_unit():
    return OrganizationalUnit(
        org_unit_id=1,
        unit_name="Department of Information and Communications Technology",
        unit_type="department",
        unit_code="DICT",
        is_active=True,
    )


def test_create_or_update_super_admin_creates_user_with_hashed_password():
    session = FakeSession([make_super_admin_role(), make_dict_unit(), None])

    result = create_or_update_super_admin(
        session,
        full_name="System Super Admin",
        email="ADMIN@EXAMPLE.TEST",
        password="correct-password",
    )

    created_user = session.added[0]

    assert result.created is True
    assert result.user is created_user
    assert created_user.email == "admin@example.test"
    assert created_user.password_hash != "correct-password"
    assert verify_password("correct-password", created_user.password_hash) is True
    assert created_user.account_status == "active"
    assert session.committed is True


def test_create_or_update_super_admin_updates_existing_user():
    existing_user = User(
        user_id=5,
        role_id=2,
        org_unit_id=None,
        full_name="Old Name",
        email="admin@example.test",
        password_hash="old-hash",
        account_status="inactive",
    )
    session = FakeSession([make_super_admin_role(), make_dict_unit(), existing_user])

    result = create_or_update_super_admin(
        session,
        full_name="System Super Admin",
        email="admin@example.test",
        password="new-password",
    )

    assert result.created is False
    assert result.user is existing_user
    assert existing_user.full_name == "System Super Admin"
    assert existing_user.role_id == 1
    assert existing_user.org_unit_id == 1
    assert existing_user.account_status == "active"
    assert verify_password("new-password", existing_user.password_hash) is True
    assert session.added == []
    assert session.committed is True


def test_create_or_update_super_admin_requires_seeded_role():
    session = FakeSession([None])

    with pytest.raises(AdminSetupError, match="super_admin role"):
        create_or_update_super_admin(
            session,
            full_name="System Super Admin",
            email="admin@example.test",
            password="password",
        )
