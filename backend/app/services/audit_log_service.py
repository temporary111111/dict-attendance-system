"""Filtered at paginated queries para sa audit-log browser."""

from dataclasses import dataclass
from datetime import date, datetime, time
from math import ceil

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import AuditLog, User


class InvalidAuditDateRangeError(Exception):
    """Raised kapag mas huli ang date_from kaysa date_to."""


@dataclass
class AuditLogPage:
    items: list[AuditLog]
    page: int
    page_size: int
    total_items: int
    total_pages: int


def list_audit_logs(
    db: Session,
    *,
    page: int,
    page_size: int,
    user_id: int | None,
    action: str | None,
    entity_type: str | None,
    entity_id: int | None,
    date_from: date | None,
    date_to: date | None,
    search: str | None,
) -> AuditLogPage:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise InvalidAuditDateRangeError

    filters = []
    if user_id is not None:
        filters.append(AuditLog.user_id == user_id)
    if action is not None:
        filters.append(AuditLog.action == action)
    if entity_type is not None:
        filters.append(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        filters.append(AuditLog.entity_id == entity_id)
    if date_from is not None:
        filters.append(
            AuditLog.created_at >= datetime.combine(date_from, time.min)
        )
    if date_to is not None:
        filters.append(
            AuditLog.created_at <= datetime.combine(date_to, time.max)
        )
    if search is not None:
        pattern = f"%{search.lower()}%"
        filters.append(
            or_(
                func.lower(AuditLog.action).like(pattern),
                func.lower(AuditLog.entity_type).like(pattern),
                func.lower(AuditLog.description).like(pattern),
                func.lower(User.full_name).like(pattern),
            )
        )

    count_statement = (
        select(func.count(AuditLog.audit_log_id))
        .select_from(AuditLog)
        .outerjoin(User, User.user_id == AuditLog.user_id)
        .where(*filters)
    )
    total_items = db.scalar(count_statement) or 0
    items = list(
        db.scalars(
            select(AuditLog)
            .outerjoin(User, User.user_id == AuditLog.user_id)
            .options(joinedload(AuditLog.user))
            .where(*filters)
            .order_by(AuditLog.created_at.desc(), AuditLog.audit_log_id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return AuditLogPage(
        items=items,
        page=page,
        page_size=page_size,
        total_items=int(total_items),
        total_pages=ceil(total_items / page_size) if total_items else 0,
    )
