"""Protected generation at download ng event attendance-sheet PDF."""

from io import BytesIO
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path as APIPath, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.responses import error_response
from app.db.session import get_db
from app.models import User
from app.services.attendance_sheet_service import (
    AttendanceSheetAccessDeniedError,
    AttendanceSheetEventNotFoundError,
    AttendanceSheetExportPersistenceError,
    AttendanceSheetGenerationError,
    generate_attendance_sheet_export,
)


router = APIRouter(tags=["attendance sheet exports"])
LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "dict-logo.png"


@router.post(
    "/events/{event_id}/attendance-sheet-exports",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Generated DICT attendance-sheet PDF.",
            "content": {"application/pdf": {}},
        }
    },
)
def generate_event_attendance_sheet(
    event_id: Annotated[int, APIPath(gt=0)],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    client_ip = request.client.host if request.client is not None else None
    try:
        result = generate_attendance_sheet_export(
            db,
            event_id,
            current_user,
            logo_path=LOGO_PATH,
            program_logo_directory=request.app.state.settings.program_logo_directory,
            signature_directory=request.app.state.settings.signature_directory,
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
        )
    except AttendanceSheetEventNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=error_response("EVENT_NOT_FOUND", "Event not found."),
        )
    except AttendanceSheetAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail=error_response(
                "FORBIDDEN",
                "You are not assigned to this program.",
            ),
        )
    except AttendanceSheetGenerationError:
        raise HTTPException(
            status_code=500,
            detail=error_response(
                "ATTENDANCE_SHEET_GENERATION_FAILED",
                "The attendance-sheet PDF could not be generated.",
            ),
        )
    except AttendanceSheetExportPersistenceError:
        raise HTTPException(
            status_code=500,
            detail=error_response(
                "ATTENDANCE_SHEET_EXPORT_FAILED",
                "The attendance-sheet export history could not be saved.",
            ),
        )

    return StreamingResponse(
        BytesIO(result.pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{result.filename}"'
            ),
            "Cache-Control": "private, no-store",
        },
    )
