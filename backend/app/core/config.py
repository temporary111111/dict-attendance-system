"""Environment settings ng backend.

Nilalagay dito ang values na nagbabago per machine, tulad ng DATABASE_URL.
"""

from functools import lru_cache

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


@lru_cache
def get_settings() -> Settings:
    """Cached settings para hindi paulit-ulit binabasa ang .env kada request."""
    return Settings()
