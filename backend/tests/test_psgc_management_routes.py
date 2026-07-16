from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import psgc_admin
from app.api.dependencies.auth import require_super_admin
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app
from app.services.psgc_management_service import PsgcPage, PsgcRecordInUseError


class RouteSession:
    pass


def make_client(*, authenticated=True):
    app = create_app(Settings(jwt_secret_key="test-secret-key-with-more-than-32-bytes"))

    def override_get_db():
        yield RouteSession()

    app.dependency_overrides[get_db] = override_get_db
    if authenticated:
        app.dependency_overrides[require_super_admin] = lambda: SimpleNamespace(
            user_id=7
        )
    return TestClient(app, raise_server_exceptions=False)


def test_super_admin_can_list_paginated_psgc_regions(monkeypatch):
    def fake_list_regions(db, *, page, page_size, status, search):
        assert page == 1
        assert page_size == 25
        assert status == "active"
        assert search == "bicol"
        return PsgcPage(
            items=[
                {
                    "level": "region",
                    "code": "0500000000",
                    "name": "Region V (Bicol Region)",
                    "is_active": True,
                    "parent_label": None,
                    "city_municipality_type": None,
                }
            ],
            page=page,
            page_size=page_size,
            total_items=1,
            total_pages=1,
        )

    monkeypatch.setattr(psgc_admin, "list_regions", fake_list_regions)
    client = make_client()

    response = client.get("/api/admin/psgc/regions?search=bicol")

    assert response.status_code == 200
    assert response.json()["data"]["pagination"] == {
        "page": 1,
        "page_size": 25,
        "total_items": 1,
        "total_pages": 1,
    }
    assert response.json()["data"]["items"][0]["code"] == "0500000000"


def test_code_update_returns_dependency_counts_when_the_record_is_in_use(monkeypatch):
    def fake_update_code(*args, **kwargs):
        raise PsgcRecordInUseError(
            child_count=3,
            attendance_address_reference_count=2,
        )

    monkeypatch.setattr(psgc_admin, "update_code", fake_update_code)
    client = make_client()

    response = client.patch(
        "/api/admin/psgc/region/0500000000/code",
        json={
            "new_code": "0500100000",
            "reason": "Verified correction.",
            "confirmed": True,
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PSGC_RECORD_IN_USE"
    assert response.json()["error"]["fields"] == {
        "child_count": 3,
        "attendance_address_reference_count": 2,
    }


def test_code_update_rejects_a_non_ten_digit_code_before_the_service_is_called():
    client = make_client()

    response = client.patch(
        "/api/admin/psgc/region/0500000000/code",
        json={
            "new_code": "bad-code",
            "reason": "Verified correction.",
            "confirmed": True,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_psgc_visual_management_requires_authentication():
    client = make_client(authenticated=False)

    response = client.get("/api/admin/psgc/regions")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
