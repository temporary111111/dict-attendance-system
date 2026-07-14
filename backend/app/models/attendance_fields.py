"""Fixed attendance fields at required/optional settings ng bawat event."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin


ATTENDANCE_FIELD_KEYS = (
    "first_name",
    "middle_name",
    "last_name",
    "suffix",
    "affiliation",
    "designation_category",
    "sex",
    "email",
    "consent_documentation_publication",
    "consent_database_processing",
    "signature",
    "psgc_address",
    "street_address",
    "postal_code",
)


class AttendanceFormField(Base):
    """System-owned definition; hindi ito admin-created custom field."""

    __tablename__ = "attendance_form_fields"
    __table_args__ = (
        UniqueConstraint(
            "display_order",
            name="uq_attendance_form_fields_display_order",
        ),
        CheckConstraint(
            "default_is_required IN (0, 1)",
            name="chk_attendance_form_fields_default_required",
        ),
        CheckConstraint(
            "is_admin_configurable IN (0, 1)",
            name="chk_attendance_form_fields_admin_configurable",
        ),
    )

    field_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    field_label: Mapped[str] = mapped_column(String(150), nullable=False)
    default_is_required: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
    )
    is_admin_configurable: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        mysql.SMALLINT(unsigned=True),
        nullable=False,
    )

    event_settings: Mapped[list["EventAttendanceFieldSetting"]] = relationship(
        "EventAttendanceFieldSetting",
        back_populates="field",
    )


class EventAttendanceFieldSetting(Base, TimestampMixin):
    """Required/optional snapshot ng isang fixed field para sa event."""

    __tablename__ = "event_attendance_field_settings"
    __table_args__ = (
        Index("idx_event_attendance_field_settings_field_key", "field_key"),
        CheckConstraint(
            "is_required IN (0, 1)",
            name="chk_event_attendance_field_settings_required",
        ),
    )

    event_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("events.event_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    field_key: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(
            "attendance_form_fields.field_key",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )
    is_required: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
    )

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="attendance_field_settings",
    )
    field: Mapped[AttendanceFormField] = relationship(
        "AttendanceFormField",
        back_populates="event_settings",
    )
