"""Main entry point ng FastAPI backend.

Nandito ang app factory para madaling gumawa ng app sa tests at sa real server.
"""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.cors import configure_cors
from app.core.exceptions import (
    api_http_exception_handler,
    api_request_validation_exception_handler,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Gumagawa ng configured FastAPI app gamit ang current environment settings."""
    current_settings = settings or get_settings()
    app = FastAPI(
        title=current_settings.app_name,
        version=current_settings.app_version,
    )
    app.state.settings = current_settings

    app.add_exception_handler(HTTPException, api_http_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        api_request_validation_exception_handler,
    )

    # Separate ang frontend sa backend, kaya kailangan configurable ang CORS.
    configure_cors(app, current_settings)
    app.include_router(api_router, prefix=current_settings.api_prefix)
    # Dito kinukuha ng frontend ang generated QR PNG gamit ang stored public path.
    app.mount(
        current_settings.qr_code_url_prefix,
        StaticFiles(
            directory=current_settings.qr_code_directory,
            check_dir=False,
        ),
        name="qr-codes",
    )
    # Dito kinukuha ng frontend at PDF renderer ang program logo images.
    app.mount(
        current_settings.program_logo_url_prefix,
        StaticFiles(
            directory=current_settings.program_logo_directory,
            check_dir=False,
        ),
        name="program-logos",
    )
    return app


app = create_app()
