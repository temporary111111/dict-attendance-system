"""Main entry point ng FastAPI backend.

Nandito ang app factory para madaling gumawa ng app sa tests at sa real server.
"""

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.cors import configure_cors


def create_app(settings: Settings | None = None) -> FastAPI:
    """Gumagawa ng configured FastAPI app gamit ang current environment settings."""
    current_settings = settings or get_settings()
    app = FastAPI(
        title=current_settings.app_name,
        version=current_settings.app_version,
    )

    # Separate ang frontend sa backend, kaya kailangan configurable ang CORS.
    configure_cors(app, current_settings)
    app.include_router(api_router, prefix=current_settings.api_prefix)
    return app


app = create_app()
