from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )

    audit_log_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(mysql.BIGINT(unsigned=True))
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    old_values_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    new_values_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")
