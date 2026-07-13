from types import SimpleNamespace

from app.core.security import hash_password
from app.services.auth_service import authenticate_admin


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


def make_user(
    password: str = "correct-password",
    account_status: str = "active",
    role_name: str = "program_admin",
):
    return SimpleNamespace(
        user_id=1,
        email="admin@example.test",
        password_hash=hash_password(password),
        account_status=account_status,
        role=SimpleNamespace(role_name=role_name, is_active=True),
    )


def test_authenticate_admin_returns_user_for_valid_active_admin():
    user = make_user()

    authenticated_user = authenticate_admin(
        FakeSession(user),
        "admin@example.test",
        "correct-password",
    )

    assert authenticated_user is user


def test_authenticate_admin_rejects_wrong_password():
    user = make_user()

    authenticated_user = authenticate_admin(
        FakeSession(user),
        "admin@example.test",
        "wrong-password",
    )

    assert authenticated_user is None


def test_authenticate_admin_rejects_inactive_user():
    user = make_user(account_status="inactive")

    authenticated_user = authenticate_admin(
        FakeSession(user),
        "admin@example.test",
        "correct-password",
    )

    assert authenticated_user is None


def test_authenticate_admin_rejects_non_admin_role():
    user = make_user(role_name="external_attendee")

    authenticated_user = authenticate_admin(
        FakeSession(user),
        "admin@example.test",
        "correct-password",
    )

    assert authenticated_user is None
