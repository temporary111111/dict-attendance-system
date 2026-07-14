"""Models para sa DICT programs, Program Admin assignments, at events."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin


class Program(Base, TimestampMixin):
    """DICT program/service tulad ng Free Wi-Fi for All or eGov Super App."""

    __tablename__ = "programs"
    __table_args__ = (
        UniqueConstraint(
            "owning_unit_id",
            "program_name",
            name="uq_programs_owning_unit_name",
        ),
        Index("idx_programs_owning_unit_id", "owning_unit_id"),
        Index("idx_programs_created_by_user_id", "created_by_user_id"),
        Index("idx_programs_program_status", "program_status"),
    )

    program_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    owning_unit_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey(
            "organizational_units.org_unit_id",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    created_by_user_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    program_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    program_status: Mapped[str] = mapped_column(
        Enum("active", "archived", name="program_status"),
        nullable=False,
        server_default="active",
    )

    owning_unit: Mapped["OrganizationalUnit"] = relationship(
        "OrganizationalUnit",
        back_populates="owned_programs",
    )
    created_by: Mapped["User"] = relationship(
        "User",
        back_populates="created_programs",
    )
    admin_assignments: Mapped[list["ProgramAdminAssignment"]] = relationship(
        "ProgramAdminAssignment",
        back_populates="program",
    )
    events: Mapped[list["Event"]] = relationship("Event", back_populates="program")


class ProgramAdminAssignment(Base):
    """Connects a Program Admin user to the program na hawak niya."""

    __tablename__ = "program_admin_assignments"
    __table_args__ = (
        # Bawal doble ang same user sa same program assignment.
        UniqueConstraint(
            "program_id",
            "user_id",
            name="uq_program_admin_assignments_program_user",
        ),
        Index("idx_program_admin_assignments_user_id", "user_id"),
        Index(
            "idx_program_admin_assignments_assigned_by_user_id",
            "assigned_by_user_id",
        ),
        Index(
            "idx_program_admin_assignments_assignment_status",
            "assignment_status",
        ),
        CheckConstraint(
            # Kapag revoked na ang assignment, kailangan may revoked_at timestamp.
            "("
            "assignment_status = 'active' AND revoked_at IS NULL"
            ") OR ("
            "assignment_status = 'revoked' AND revoked_at IS NOT NULL"
            ")",
            name="chk_program_admin_assignments_revoked_at",
        ),
    )

    assignment_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    program_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("programs.program_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_by_user_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    assignment_status: Mapped[str] = mapped_column(
        Enum("active", "revoked", name="assignment_status"),
        nullable=False,
        server_default="active",
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)

    program: Mapped[Program] = relationship(
        "Program",
        back_populates="admin_assignments",
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="program_admin_assignments",
    )
    assigned_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[assigned_by_user_id],
        back_populates="assigned_program_admin_assignments",
    )


class Event(Base, TimestampMixin):
    """Specific activity under a program, created by an assigned Program Admin."""

    __tablename__ = "events"
    __table_args__ = (
        # Event code ang stable identifier para sa public attendance link/QR.
        UniqueConstraint("event_code", name="uq_events_event_code"),
        Index("idx_events_program_id", "program_id"),
        Index("idx_events_created_by_user_id", "created_by_user_id"),
        Index("idx_events_event_date", "event_date"),
        Index("idx_events_event_status", "event_status"),
        CheckConstraint(
            "(event_status <> 'open' OR opened_at IS NOT NULL) "
            "AND (event_status <> 'closed' OR closed_at IS NOT NULL)",
            name="chk_events_status_dates",
        ),
    )

    event_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    program_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("programs.program_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    created_by_user_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    event_title: Mapped[str] = mapped_column(String(200), nullable=False)
    event_description: Mapped[str | None] = mapped_column(Text)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_code: Mapped[str] = mapped_column(String(100), nullable=False)
    public_attendance_url: Mapped[str | None] = mapped_column(String(500))
    qr_code_path: Mapped[str | None] = mapped_column(String(500))
    event_status: Mapped[str] = mapped_column(
        Enum("draft", "open", "closed", "archived", name="event_status"),
        nullable=False,
        server_default="draft",
    )
    opened_at: Mapped[datetime | None] = mapped_column(DateTime)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)

    program: Mapped[Program] = relationship("Program", back_populates="events")
    created_by: Mapped["User"] = relationship(
        "User",
        back_populates="created_events",
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="event",
    )
    attendance_sheet_exports: Mapped[list["AttendanceSheetExport"]] = relationship(
        "AttendanceSheetExport",
        back_populates="event",
    )
    attendance_field_settings: Mapped[list["EventAttendanceFieldSetting"]] = (
        relationship(
            "EventAttendanceFieldSetting",
            back_populates="event",
            cascade="all, delete-orphan",
        )
    )
