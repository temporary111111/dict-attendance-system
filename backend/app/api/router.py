from fastapi import APIRouter

from app.api.audit_logs import router as audit_logs_router
from app.api.attendance_records import router as attendance_records_router
from app.api.attendance_field_settings import router as attendance_field_settings_router
from app.api.attendance_sheet_exports import router as attendance_sheet_exports_router
from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.health import router as health_router
from app.api.program_assignments import router as program_assignments_router
from app.api.programs import router as programs_router
from app.api.psgc import router as psgc_router
from app.api.public_attendance import router as public_attendance_router
from app.api.reference_data import router as reference_data_router
from app.api.reports import router as reports_router
from app.api.users import router as users_router

api_router = APIRouter()
api_router.include_router(audit_logs_router)
api_router.include_router(attendance_field_settings_router)
api_router.include_router(attendance_records_router)
api_router.include_router(attendance_sheet_exports_router)
api_router.include_router(auth_router)
api_router.include_router(events_router)
api_router.include_router(health_router)
api_router.include_router(programs_router)
api_router.include_router(program_assignments_router)
api_router.include_router(psgc_router)
api_router.include_router(public_attendance_router)
api_router.include_router(reference_data_router)
api_router.include_router(reports_router)
api_router.include_router(users_router)
