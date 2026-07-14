"""Super Admin route para sa filtered audit-log history."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.core.responses import error_response, success_response
from app.db.session import get_db
from app.schemas.audit_logs import AuditLogListResponse
from app.services.audit_log_service import (
    InvalidAuditDateRangeError,
    list_audit_logs,
)

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit logs"],
    dependencies=[Depends(require_super_admin)],
)


def _audit_log_data(audit_log) -> dict[str, Any]:
    actor = None
    if audit_log.user is not None:
        actor = {
            "user_id": audit_log.user.user_id,
            "full_name": audit_log.user.full_name,
        }
    return {
        "audit_log_id": audit_log.audit_log_id,
        "actor": actor,
        "action": audit_log.action,
        "entity_type": audit_log.entity_type,
        "entity_id": audit_log.entity_id,
        "description": audit_log.description,
        "old_values": audit_log.old_values_json,
        "new_values": audit_log.new_values_json,
        "ip_address": audit_log.ip_address,
        "user_agent": audit_log.user_agent,
        "created_at": audit_log.created_at,
    }


@router.get("", response_model=AuditLogListResponse)
def get_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 25,
    user_id: Annotated[int | None, Query(alias="userId", gt=0)] = None,
    action: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    entity_type: Annotated[
        str | None,
        Query(alias="entityType", min_length=1, max_length=100),
    ] = None,
    entity_id: Annotated[int | None, Query(alias="entityId", gt=0)] = None,
    date_from: Annotated[date | None, Query(alias="dateFrom")] = None,
    date_to: Annotated[date | None, Query(alias="dateTo")] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
) -> dict[str, Any]:
    normalized_action = action.strip() or None if action else None
    normalized_entity_type = entity_type.strip() or None if entity_type else None
    normalized_search = search.strip() or None if search else None
    try:
        result = list_audit_logs(
            db,
            page=page,
            page_size=page_size,
            user_id=user_id,
            action=normalized_action,
            entity_type=normalized_entity_type,
            entity_id=entity_id,
            date_from=date_from,
            date_to=date_to,
            search=normalized_search,
        )
    except InvalidAuditDateRangeError:
        raise HTTPException(
            status_code=422,
            detail=error_response(
                "INVALID_DATE_RANGE",
                "dateFrom must not be later than dateTo.",
                {"dateFrom": "Select a date on or before dateTo."},
            ),
        )

    return success_response(
        {
            "items": [_audit_log_data(item) for item in result.items],
            "pagination": {
                "page": result.page,
                "page_size": result.page_size,
                "total_items": result.total_items,
                "total_pages": result.total_pages,
            },
        },
        "Audit logs retrieved.",
    )
