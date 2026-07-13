import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_parse_comma_separated_cors_origins():
    settings = Settings(
        cors_origins="http://localhost:5500, http://127.0.0.1:5500"
    )

    assert settings.cors_origins == [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]


def test_settings_keep_list_cors_origins():
    settings = Settings(cors_origins=["http://example.test"])

    assert settings.cors_origins == ["http://example.test"]


def test_settings_require_event_code_placeholder_in_public_url_template():
    with pytest.raises(ValidationError):
        Settings(public_attendance_url_template="http://frontend/attendance")
