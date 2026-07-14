from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app


PUBLIC_REQUIREMENTS = {
    "first_name": True,
    "middle_name": False,
    "last_name": True,
    "suffix": False,
    "affiliation": True,
    "designation_category": True,
    "sex": True,
    "email": True,
    "consent_documentation_publication": True,
    "consent_database_processing": True,
    "signature": False,
    "psgc_address": False,
    "street_address": False,
    "postal_code": False,
}


class FakeSession:
    def __init__(self, *, event=None, records=None):
        self.event = event
        self.records = records or []
        self.scalar_statement = None
        self.scalars_statement = None

    def scalar(self, statement):
        self.scalar_statement = str(statement)
        return self.event

    def scalars(self, statement):
        self.scalars_statement = str(statement)
        return SimpleNamespace(all=lambda: self.records)


def make_settings() -> Settings:
    return Settings(jwt_secret_key="test-secret-key-with-more-than-32-bytes")


def make_client(session) -> TestClient:
    app = create_app(make_settings())

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def make_public_event(status="open"):
    return SimpleNamespace(
        event_code="public-code",
        event_title="Digital Inclusion Orientation",
        event_description="Community orientation.",
        venue="DICT Regional Office",
        event_date=date(2026, 8, 15),
        event_status=status,
        attendance_field_settings=[
            SimpleNamespace(field_key=key, is_required=value)
            for key, value in PUBLIC_REQUIREMENTS.items()
        ],
        program=SimpleNamespace(
            program_id=3,
            program_name="Free Wi-Fi for All",
        ),
    )


def test_get_public_event_returns_safe_open_event_details_without_auth():
    session = FakeSession(event=make_public_event())
    client = make_client(session)

    response = client.get("/api/public/events/public-code")

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "event_code": "public-code",
            "event_title": "Digital Inclusion Orientation",
            "event_description": "Community orientation.",
            "venue": "DICT Regional Office",
            "event_date": "2026-08-15",
            "event_status": "open",
            "accepting_attendance": True,
            "attendance_field_requirements": PUBLIC_REQUIREMENTS,
            "program": {
                "program_id": 3,
                "program_name": "Free Wi-Fi for All",
            },
        },
        "message": "Public event retrieved.",
    }
    assert "events.event_status !=" in session.scalar_statement


def test_get_public_event_marks_closed_event_as_not_accepting():
    client = make_client(FakeSession(event=make_public_event("closed")))

    response = client.get("/api/public/events/public-code")

    assert response.status_code == 200
    assert response.json()["data"]["accepting_attendance"] is False


def test_get_public_event_returns_not_found_for_unknown_or_archived_code():
    client = make_client(FakeSession(event=None))

    response = client.get("/api/public/events/unknown")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PUBLIC_EVENT_NOT_FOUND"


def test_list_psgc_regions_returns_active_options():
    session = FakeSession(
        records=[SimpleNamespace(region_code="0300000000", region_name="Region III")]
    )
    client = make_client(session)

    response = client.get("/api/psgc/regions")

    assert response.status_code == 200
    assert response.json()["data"] == [
        {"region_code": "0300000000", "region_name": "Region III"}
    ]
    assert "is_active" in session.scalars_statement


def test_list_psgc_provinces_filters_by_region_code():
    session = FakeSession(
        records=[
            SimpleNamespace(
                province_code="0354000000",
                region_code="0300000000",
                province_name="Pampanga",
            )
        ]
    )
    client = make_client(session)

    response = client.get(
        "/api/psgc/provinces",
        params={"regionCode": "0300000000"},
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["province_name"] == "Pampanga"
    assert "region_code" in session.scalars_statement


def test_list_psgc_cities_filters_region_and_optional_province():
    session = FakeSession(
        records=[
            SimpleNamespace(
                city_municipality_code="0354160000",
                region_code="0300000000",
                province_code="0354000000",
                city_municipality_name="City of San Fernando",
                city_municipality_type="city",
            )
        ]
    )
    client = make_client(session)

    response = client.get(
        "/api/psgc/cities-municipalities",
        params={
            "regionCode": "0300000000",
            "provinceCode": "0354000000",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["city_municipality_type"] == "city"
    assert "province_code" in session.scalars_statement


def test_list_psgc_barangays_filters_by_city_municipality():
    session = FakeSession(
        records=[
            SimpleNamespace(
                barangay_code="0354160010",
                city_municipality_code="0354160000",
                barangay_name="San Agustin",
            )
        ]
    )
    client = make_client(session)

    response = client.get(
        "/api/psgc/barangays",
        params={"cityMunicipalityCode": "0354160000"},
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["barangay_name"] == "San Agustin"
    assert "city_municipality_code" in session.scalars_statement


def test_psgc_child_lookup_requires_parent_query_parameter():
    client = make_client(FakeSession())

    response = client.get("/api/psgc/provinces")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
