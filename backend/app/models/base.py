"""Declarative base and shared mixins."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, MetaData, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# measured   = value measured in an experiment
# simulated  = value produced by a numerical model
# derived    = statistic or aggregate computed from other data
RECORD_KINDS = ("measured", "simulated", "derived")
RECORD_KIND_CHECK = "record_kind IN ('measured','simulated','derived')"


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProvenanceMixin:
    """Every scientific row records where it came from."""

    dataset_version_id: Mapped[int] = mapped_column(ForeignKey("dataset_versions.id"), index=True)
    source_file: Mapped[str] = mapped_column(String(512))
    # CSV line number in source_file (header = line 1)
    source_row: Mapped[int | None] = mapped_column(Integer)
    # Original NASA file named inside a derived/tidy file, if any
    upstream_file: Mapped[str | None] = mapped_column(String(512))
    record_kind: Mapped[str] = mapped_column(String(16))
