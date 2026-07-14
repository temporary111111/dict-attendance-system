"""Response contracts para sa Super Admin audit-log browser."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditActorData(BaseModel):
    user_id: int
    full_name: str


class AuditLogData(BaseModel):
    audit_log_id: int
    actor: AuditActorData | None
    action: str
    entity_type: str
    entity_id: int | None
    description: str
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class AuditPaginationData(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class AuditLogListData(BaseModel):
    items: list[AuditLogData]
    pagination: AuditPaginationData


class AuditLogListResponse(BaseModel):
    data: AuditLogListData
    message: str
