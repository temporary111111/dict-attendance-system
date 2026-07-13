from __future__ import annotations

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin


class PSGCRegion(Base, TimestampMixin):
    __tablename__ = "psgc_regions"
    __table_args__ = (
        Index("idx_psgc_regions_is_active", "is_active"),
        CheckConstraint("is_active IN (0, 1)", name="chk_psgc_regions_is_active"),
    )

    region_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    region_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
        server_default=text("1"),
    )

    provinces: Mapped[list["PSGCProvince"]] = relationship(
        "PSGCProvince",
        back_populates="region",
    )
    cities_municipalities: Mapped[list["PSGCCityMunicipality"]] = relationship(
        "PSGCCityMunicipality",
        back_populates="region",
    )
    attendance_record_addresses: Mapped[list["AttendanceRecordAddress"]] = (
        relationship(
            "AttendanceRecordAddress",
            back_populates="region",
        )
    )


class PSGCProvince(Base, TimestampMixin):
    __tablename__ = "psgc_provinces"
    __table_args__ = (
        Index("idx_psgc_provinces_region_code", "region_code"),
        Index("idx_psgc_provinces_is_active", "is_active"),
        CheckConstraint("is_active IN (0, 1)", name="chk_psgc_provinces_is_active"),
    )

    province_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    region_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("psgc_regions.region_code", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    province_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
        server_default=text("1"),
    )

    region: Mapped[PSGCRegion] = relationship(
        "PSGCRegion",
        back_populates="provinces",
    )
    cities_municipalities: Mapped[list["PSGCCityMunicipality"]] = relationship(
        "PSGCCityMunicipality",
        back_populates="province",
    )
    attendance_record_addresses: Mapped[list["AttendanceRecordAddress"]] = (
        relationship(
            "AttendanceRecordAddress",
            back_populates="province",
        )
    )


class PSGCCityMunicipality(Base, TimestampMixin):
    __tablename__ = "psgc_cities_municipalities"
    __table_args__ = (
        Index("idx_psgc_cities_municipalities_region_code", "region_code"),
        Index("idx_psgc_cities_municipalities_province_code", "province_code"),
        Index("idx_psgc_cities_municipalities_is_active", "is_active"),
        CheckConstraint(
            "is_active IN (0, 1)",
            name="chk_psgc_cities_municipalities_is_active",
        ),
    )

    city_municipality_code: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
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
    city_municipality_name: Mapped[str] = mapped_column(String(150), nullable=False)
    city_municipality_type: Mapped[str] = mapped_column(
        Enum("city", "municipality", name="city_municipality_type"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
        server_default=text("1"),
    )

    region: Mapped[PSGCRegion] = relationship(
        "PSGCRegion",
        back_populates="cities_municipalities",
    )
    province: Mapped[PSGCProvince | None] = relationship(
        "PSGCProvince",
        back_populates="cities_municipalities",
    )
    barangays: Mapped[list["PSGCBarangay"]] = relationship(
        "PSGCBarangay",
        back_populates="city_municipality",
    )
    attendance_record_addresses: Mapped[list["AttendanceRecordAddress"]] = (
        relationship(
            "AttendanceRecordAddress",
            back_populates="city_municipality",
        )
    )


class PSGCBarangay(Base, TimestampMixin):
    __tablename__ = "psgc_barangays"
    __table_args__ = (
        Index("idx_psgc_barangays_city_municipality_code", "city_municipality_code"),
        Index("idx_psgc_barangays_is_active", "is_active"),
        CheckConstraint("is_active IN (0, 1)", name="chk_psgc_barangays_is_active"),
    )

    barangay_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    city_municipality_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey(
            "psgc_cities_municipalities.city_municipality_code",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    barangay_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        mysql.TINYINT(1),
        nullable=False,
        server_default=text("1"),
    )

    city_municipality: Mapped[PSGCCityMunicipality] = relationship(
        "PSGCCityMunicipality",
        back_populates="barangays",
    )
    attendance_record_addresses: Mapped[list["AttendanceRecordAddress"]] = (
        relationship(
            "AttendanceRecordAddress",
            back_populates="barangay",
        )
    )
