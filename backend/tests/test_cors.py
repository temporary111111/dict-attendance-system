from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_configured_origin_is_allowed_by_cors():
    app = create_app(Settings(cors_origins=["http://frontend.test"]))
    client = TestClient(app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://frontend.test",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://frontend.test"

