"""Models para sa public attendance submissions, addresses, at report exports."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin


class AttendanceRecord(Base, TimestampMixin):
    """Isang attendance submission ng attendee para sa isang event."""

    __tablename__ = "attendance_records"
    __table_args__ = (
        # Bawal maulit ang same email sa same event para mabawasan ang duplicates.
        UniqueConstraint(
            "event_id",
            "email",
            name="uq_attendance_records_event_email",
        ),
        Index("idx_attendance_records_event_id", "event_id"),
        Index("idx_attendance_records_email", "email"),
        Index("idx_attendance_records_status", "attendance_status"),
        Index("idx_attendance_records_duplicate_flag", "duplicate_flag"),
        Index("idx_attendance_records_submitted_at", "submitted_at"),
        CheckConstraint(
            "consent_documentation_publication IN (0, 1)",
            name="chk_attendance_records_consent_documentation",
        ),
        CheckConstraint(
            "consent_database_processing IN (0, 1)",
            name="chk_attendance_records_consent_database",
        ),
        CheckConstraint(
            "duplicate_flag IN (0, 1)",
            name="chk_attendance_records_duplicate_flag",
        ),
    )

    attendance_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    event_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("events.event_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    suffix: Mapped[str | None] = mapped_column(String(30))
    # General term ito para pwede students, government officials, employees, etc.
    affiliation: Mapped[str] = mapped_column(String(200), nullable=False)
    designation_category: Mapped[str] = mapped_column(String(150), nullable=False)
    sex: Mapped[str] = mapped_column(Enum("F", "M", name="sex"), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    consent_documentation_publication: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
        server_default=text("0"),
    )
    consent_database_processing: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
        server_default=text("0"),
    )
    signature_text: Mapped[str | None] = mapped_column(String(150))
    signature_image_path: Mapped[str | None] = mapped_column(String(500))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    attendance_status: Mapped[str] = mapped_column(
        Enum("valid", "duplicate", "invalid", "void", name="attendance_status"),
        nullable=False,
        server_default="valid",
    )
    duplicate_flag: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
        server_default=text("0"),
    )

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="attendance_records",
    )
    # One-to-one shortcut: attendance.address returns the separate address row.
    address: Mapped["AttendanceRecordAddress | None"] = relationship(
        "AttendanceRecordAddress",
        back_populates="attendance",
        cascade="all, delete-orphan",
        uselist=False,
    )


class AttendanceSheetExport(Base):
    """History ng generated/downloaded attendance sheet after or during an event."""

    __tablename__ = "attendance_sheet_exports"
    __table_args__ = (
        Index("idx_attendance_sheet_exports_event_id", "event_id"),
        Index(
            "idx_attendance_sheet_exports_exported_by_user_id",
            "exported_by_user_id",
        ),
        Index("idx_attendance_sheet_exports_exported_at", "exported_at"),
    )

    export_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    event_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("events.event_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    exported_by_user_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    export_format: Mapped[str] = mapped_column(
        Enum("pdf", "xlsx", "csv", name="export_format"),
        nullable=False,
        server_default="pdf",
    )
    file_path: Mapped[str | None] = mapped_column(String(500))
    total_records: Mapped[int] = mapped_column(
        mysql.INTEGER(unsigned=True),
        nullable=False,
        server_default=text("0"),
    )
    exported_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="attendance_sheet_exports",
    )
    exported_by: Mapped["User"] = relationship(
        "User",
        back_populates="attendance_sheet_exports",
    )


class AttendanceRecordAddress(Base, TimestampMixin):
    """Address details ng attendee, separated para normalized ang attendance data."""

    __tablename__ = "attendance_record_addresses"
    __table_args__ = (
        # One address row lang per attendance record.
        UniqueConstraint(
            "attendance_id",
            name="uq_attendance_record_addresses_attendance_id",
        ),
        Index("idx_attendance_record_addresses_region_code", "region_code"),
        Index("idx_attendance_record_addresses_province_code", "province_code"),
        Index(
            "idx_attendance_record_addresses_city_municipality_code",
            "city_municipality_code",
        ),
        Index("idx_attendance_record_addresses_barangay_code", "barangay_code"),
    )

    address_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    attendance_id: Mapped[int] = mapped_column(
        mysql.BIGINT(unsigned=True),
        ForeignKey(
            "attendance_records.attendance_id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    region_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("psgc_regions.region_code", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    province_code: Mapped[str | None] = mapped_column(
        String(10),
        ForeignKey(
            "psgc_provinces.province_code",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
    )
    city_municipality_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey(
            "psgc_cities_municipalities.city_municipality_code",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    barangay_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("psgc_barangays.barangay_code", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    street_address: Mapped[str | None] = mapped_column(String(255))
    postal_code: Mapped[str | None] = mapped_column(String(10))

    attendance: Mapped[AttendanceRecord] = relationship(
        "AttendanceRecord",
        back_populates="address",
    )
    region: Mapped["PSGCRegion"] = relationship(
        "PSGCRegion",
        back_populates="attendance_record_addresses",
    )
    province: Mapped["PSGCProvince | None"] = relationship(
        "PSGCProvince",
        back_populates="attendance_record_addresses",
    )
    city_municipality: Mapped["PSGCCityMunicipality"] = relationship(
        "PSGCCityMunicipality",
        back_populates="attendance_record_addresses",
    )
    barangay: Mapped["PSGCBarangay"] = relationship(
        "PSGCBarangay",
        back_populates="attendance_record_addresses",
    )
