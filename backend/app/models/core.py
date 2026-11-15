"""Users, investigations, sources, dataset versions, reference tables, logs."""
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Investigation(Base, TimestampMixin):
    __tablename__ = "investigations"
    id: Mapped[int] = mapped_column(primary_key=True)
    psi_id: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    acronym: Mapped[str | None] = mapped_column(String(64))
    title: Mapped[str | None] = mapped_column(String(512))
    research_area: Mapped[str | None] = mapped_column(String(64))
    doi: Mapped[str | None] = mapped_column(String(128))
    page_url: Mapped[str | None] = mapped_column(String(512))
    license: Mapped[str | None] = mapped_column(String(64))
    # How the PSI id <-> name mapping was established
    id_verification: Mapped[str] = mapped_column(String(32))
    availability_status: Mapped[str] = mapped_column(String(32), default="not_retrieved")
    availability_note: Mapped[str | None] = mapped_column(Text)
    sources: Mapped[list["NasaSource"]] = relationship(back_populates="investigation")


class NasaSource(Base, TimestampMixin):
    """A concrete file that was supplied for an investigation."""

    __tablename__ = "nasa_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id"), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    origin: Mapped[str] = mapped_column(String(32))  # e.g. user_supplied, nasa_psi_download
    is_derived: Mapped[bool] = mapped_column(Boolean)  # True if not an original NASA table/file
    doi: Mapped[str | None] = mapped_column(String(128))
    url: Mapped[str | None] = mapped_column(String(1024))
    raw_path: Mapped[str] = mapped_column(String(1024))
    investigation: Mapped[Investigation] = relationship(back_populates="sources")
    versions: Mapped[list["DatasetVersion"]] = relationship(back_populates="source")


class DatasetVersion(Base, TimestampMixin):
    """One ingestion run of one source file with one parser."""

    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint("source_id", "parser_name", "parser_version", name="uq_dataset_versions_source_parser"),
        CheckConstraint("status IN ('processing','completed','failed')", name="status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("nasa_sources.id"), index=True)
    parser_name: Mapped[str] = mapped_column(String(64))
    parser_version: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="processing")
    rows_read: Mapped[int | None] = mapped_column(Integer)
    records_stored: Mapped[int | None] = mapped_column(Integer)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[NasaSource] = relationship(back_populates="versions")
    issues: Mapped[list["IngestionIssue"]] = relationship(back_populates="dataset_version")


class IngestionIssue(Base, TimestampMixin):
    """Missing values, duplicates, unit gaps, link failures, processing errors."""

    __tablename__ = "ingestion_issues"
    __table_args__ = (CheckConstraint("severity IN ('info','warning','error')", name="severity"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_version_id: Mapped[int] = mapped_column(ForeignKey("dataset_versions.id"), index=True)
    severity: Mapped[str] = mapped_column(String(8))
    code: Mapped[str] = mapped_column(String(48), index=True)
    message: Mapped[str] = mapped_column(Text)
    source_row: Mapped[int | None] = mapped_column(Integer)
    column_name: Mapped[str | None] = mapped_column(String(128))
    dataset_version: Mapped[DatasetVersion] = relationship(back_populates="issues")


class Material(Base, TimestampMixin):
    __tablename__ = "materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(64))


class Fuel(Base, TimestampMixin):
    __tablename__ = "fuels"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    formula: Mapped[str | None] = mapped_column(String(64))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[dict | None] = mapped_column(JSON)
