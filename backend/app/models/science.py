"""Experiments, conditions and measurements. Doubles (not fixed Numeric) because
values span ~1e-29 to ~1e9; original and normalized values are stored side by side."""
from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import RECORD_KIND_CHECK, Base, ProvenanceMixin, TimestampMixin


class Experiment(Base, TimestampMixin, ProvenanceMixin):
    __tablename__ = "experiments"
    __table_args__ = (
        UniqueConstraint("investigation_id", "material_id", "test_label", name="uq_experiments_inv_material_label"),
        CheckConstraint(RECORD_KIND_CHECK, name="record_kind"),
        CheckConstraint(
            "gravity_environment IS NULL OR gravity_environment IN ('microgravity','normal_gravity')",
            name="gravity_environment",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id"), index=True)
    test_label: Mapped[str] = mapped_column(String(256))
    parent_experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id"), index=True)
    material_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id"), index=True)
    fuel_id: Mapped[int | None] = mapped_column(ForeignKey("fuels.id"), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    # Kept as text: the source gives day-month without a year; none is assumed.
    date_text: Mapped[str | None] = mapped_column(String(32))
    # NULL unless the source states it; never inferred.
    gravity_environment: Mapped[str | None] = mapped_column(String(16))


class _ValueColumns(ProvenanceMixin):
    value_original: Mapped[float | None] = mapped_column(Float(53))
    unit_original: Mapped[str | None] = mapped_column(String(32))
    value_normalized: Mapped[float | None] = mapped_column(Float(53))
    unit_normalized: Mapped[str | None] = mapped_column(String(32))


class ExperimentalCondition(Base, TimestampMixin, _ValueColumns):
    __tablename__ = "experimental_conditions"
    __table_args__ = (CheckConstraint(RECORD_KIND_CHECK, name="record_kind"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)


class _MeasurementColumns(_ValueColumns):
    variable: Mapped[str] = mapped_column(String(96), index=True)
    variable_original: Mapped[str | None] = mapped_column(String(96))
    statistic: Mapped[str | None] = mapped_column(String(32))
    qualifier: Mapped[str | None] = mapped_column(String(256))


class CombustionMeasurement(Base, TimestampMixin, _MeasurementColumns):
    __tablename__ = "combustion_measurements"
    __table_args__ = (CheckConstraint(RECORD_KIND_CHECK, name="record_kind"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    # NULL for loose records (e.g. summary statistics of a whole output file)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id"), index=True)


class SmokeMeasurement(Base, TimestampMixin, _MeasurementColumns):
    __tablename__ = "smoke_measurements"
    __table_args__ = (
        CheckConstraint(RECORD_KIND_CHECK, name="record_kind"),
        Index("ix_smoke_measurements_experiment_variable", "experiment_id", "variable"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id"), index=True)
