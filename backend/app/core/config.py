"""Environment settings ng backend.

Nilalagay dito ang values na nagbabago per machine, tulad ng DATABASE_URL.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings galing defaults, environment variables, at .env file."""

    app_name: str = "DICT Attendance System API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str = (
        "mysql+pymysql://root:password@localhost:3306/"
        "dict_attendance_system?charset=utf8mb4"
    )
    jwt_secret_key: str = "change-this-development-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480
    public_attendance_url_template: str = (
        "http://127.0.0.1:5500/attendance.html?event={event_code}"
    )
    qr_code_directory: Path = Path("storage/qr_codes")
    qr_code_url_prefix: str = "/media/qr-codes"
    signature_directory: Path = Path("storage/signatures")
    signature_max_bytes: int = 5 * 1024 * 1024
    program_logo_directory: Path = Path("storage/program_logos")
    program_logo_max_bytes: int = 2 * 1024 * 1024
    program_logo_url_prefix: str = "/media/program-logos"
    psgc_import_max_bytes: int = 10 * 1024 * 1024
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5500",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Tumatanggap ng comma-separated CORS origins para madali i-edit sa .env."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("public_attendance_url_template")
    @classmethod
    def validate_public_attendance_url_template(cls, value: str) -> str:
        """Kailangan ang placeholder para mailagay ang rotated event code."""
        if "{event_code}" not in value:
            raise ValueError("URL template must contain {event_code}.")
        return value

    @field_validator("qr_code_url_prefix")
    @classmethod
    def normalize_qr_code_url_prefix(cls, value: str) -> str:
        normalized = "/" + value.strip().strip("/")
        if normalized == "/":
            raise ValueError("QR code URL prefix cannot be empty.")
        return normalized

    @field_validator("program_logo_url_prefix")
    @classmethod
    def normalize_program_logo_url_prefix(cls, value: str) -> str:
        normalized = "/" + value.strip().strip("/")
        if normalized == "/":
            raise ValueError("Program logo URL prefix cannot be empty.")
        return normalized


@lru_cache
def get_settings() -> Settings:
    """Cached settings para hindi paulit-ulit binabasa ang .env kada request."""
    return Settings()
