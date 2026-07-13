from __future__ import annotations

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin


class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("role_name", name="uq_roles_role_name"),
        CheckConstraint("is_active IN (0, 1)", name="chk_roles_is_active"),
    )

    role_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
        server_default=text("1"),
    )

    users: Mapped[list["User"]] = relationship("User", back_populates="role")


class OrganizationalUnit(Base, TimestampMixin):
    __tablename__ = "organizational_units"
    __table_args__ = (
        UniqueConstraint("unit_code", name="uq_organizational_units_unit_code"),
        Index("idx_organizational_units_parent_unit_id", "parent_unit_id"),
        Index("idx_organizational_units_unit_type", "unit_type"),
        CheckConstraint(
            "is_active IN (0, 1)",
            name="chk_organizational_units_is_active",
        ),
    )

    org_unit_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    parent_unit_id: Mapped[int | None] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey(
            "organizational_units.org_unit_id",
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
    )
    unit_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_code: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
        server_default=text("1"),
    )

    parent: Mapped["OrganizationalUnit | None"] = relationship(
        "OrganizationalUnit",
        back_populates="children",
        remote_side=[org_unit_id],
    )
    children: Mapped[list["OrganizationalUnit"]] = relationship(
        "OrganizationalUnit",
        back_populates="parent",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="org_unit",
    )
    owned_programs: Mapped[list["Program"]] = relationship(
        "Program",
        back_populates="owning_unit",
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("idx_users_role_id", "role_id"),
        Index("idx_users_org_unit_id", "org_unit_id"),
        Index("idx_users_account_status", "account_status"),
    )

    user_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    role_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("roles.role_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    org_unit_id: Mapped[int | None] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey(
            "organizational_units.org_unit_id",
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    account_status: Mapped[str] = mapped_column(
        Enum("active", "inactive", name="user_account_status"),
        nullable=False,
        server_default="active",
    )

    role: Mapped[Role] = relationship("Role", back_populates="users")
    org_unit: Mapped[OrganizationalUnit | None] = relationship(
        "OrganizationalUnit",
        back_populates="users",
    )
    created_programs: Mapped[list["Program"]] = relationship(
        "Program",
        back_populates="created_by",
    )
    program_admin_assignments: Mapped[list["ProgramAdminAssignment"]] = (
        relationship(
            "ProgramAdminAssignment",
            foreign_keys="ProgramAdminAssignment.user_id",
            back_populates="user",
        )
    )
    assigned_program_admin_assignments: Mapped[
        list["ProgramAdminAssignment"]
    ] = relationship(
        "ProgramAdminAssignment",
        foreign_keys="ProgramAdminAssignment.assigned_by_user_id",
        back_populates="assigned_by",
    )
    created_events: Mapped[list["Event"]] = relationship(
        "Event",
        back_populates="created_by",
    )
    attendance_sheet_exports: Mapped[list["AttendanceSheetExport"]] = (
        relationship(
            "AttendanceSheetExport",
            back_populates="exported_by",
        )
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
    )
