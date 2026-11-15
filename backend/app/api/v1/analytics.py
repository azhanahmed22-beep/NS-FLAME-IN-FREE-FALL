import math
from collections.abc import Iterable

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import (
    CombustionMeasurement,
    DatasetVersion,
    Experiment,
    Investigation,
    Material,
    NasaSource,
    SmokeMeasurement,
)
from app.schemas.workspace import ChartPoint, ChartResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _chart(
    points: Iterable[tuple[str, float | None]],
    *,
    source: str,
    unit: str | None = None,
) -> ChartResponse:
    return ChartResponse(
        points=[
            ChartPoint(label=label, value=value)
            for label, value in points
            if value is not None and math.isfinite(value)
        ],
        unit=unit,
        source=source,
    )


@router.get("/combustion", response_model=ChartResponse)
def combustion_chart(db: Session = Depends(get_db)) -> ChartResponse:
    records = db.scalars(
        select(CombustionMeasurement)
        .where(
            CombustionMeasurement.variable == "extinction_diameter_cool",
            CombustionMeasurement.record_kind == "measured",
        )
        .order_by(CombustionMeasurement.source_row, CombustionMeasurement.id)
        .limit(200)
    ).all()
    return _chart(
        (
            (f"{record.source_file}:{record.source_row or record.id}", record.value_original)
            for record in records
        ),
        source="PSI-117 measured extinction_diameter_cool records; the source does not specify a unit.",
    )


@router.get("/materials", response_model=ChartResponse)
def material_chart(db: Session = Depends(get_db)) -> ChartResponse:
    statement = (
        select(Material.name, func.avg(SmokeMeasurement.value_original))
        .join(Experiment, Experiment.material_id == Material.id)
        .join(SmokeMeasurement, SmokeMeasurement.experiment_id == Experiment.id)
        .where(
            SmokeMeasurement.variable == "obscuration_drop_median",
            SmokeMeasurement.record_kind == "derived",
        )
        .group_by(Material.name)
        .order_by(Material.name)
    )
    return _chart(
        ((name, float(value) if value is not None else None) for name, value in db.execute(statement)),
        unit="V",
        source="Mean of derived SAME-R per-test obscuration-drop medians, grouped by material.",
    )


@router.get("/microgravity", response_model=ChartResponse)
def microgravity_chart(db: Session = Depends(get_db)) -> ChartResponse:
    records = db.scalars(
        select(SmokeMeasurement)
        .where(
            SmokeMeasurement.variable == "NumDen",
            SmokeMeasurement.statistic == "mean",
            SmokeMeasurement.record_kind == "derived",
        )
        .order_by(SmokeMeasurement.source_row, SmokeMeasurement.id)
        .limit(200)
    ).all()
    points: list[tuple[str, float | None]] = []
    for record in records:
        labels = dict(
            part.split("=", 1)
            for part in (record.qualifier or "").split(";")
            if "=" in part
        )
        case = labels.get("case", "case unspecified")
        gravity = labels.get("gravity", "gravity unspecified")
        points.append((f"{case} · {gravity}", record.value_original))
    return _chart(
        points,
        source="PSI-115 derived NumDen means; the source does not specify a unit. Gravity labels are source-provided.",
    )


@router.get("/overview", response_model=ChartResponse)
def overview_chart(db: Session = Depends(get_db)) -> ChartResponse:
    statement = (
        select(Investigation.psi_id, NasaSource.filename, DatasetVersion.records_stored)
        .join(NasaSource, NasaSource.investigation_id == Investigation.id)
        .join(DatasetVersion, DatasetVersion.source_id == NasaSource.id)
        .where(DatasetVersion.status == "completed")
        .order_by(Investigation.psi_id, NasaSource.filename)
    )
    return _chart(
        (
            (f"{psi_id} · {filename}", float(count or 0))
            for psi_id, filename, count in db.execute(statement)
        ),
        unit="records",
        source="Completed dataset ingestion metadata; values are stored-record counts, not experimental measurements.",
    )


@router.get("/smoke", response_model=ChartResponse)
def smoke_chart(db: Session = Depends(get_db)) -> ChartResponse:
    statement = (
        select(SmokeMeasurement, Experiment, Material)
        .join(Experiment, SmokeMeasurement.experiment_id == Experiment.id)
        .outerjoin(Material, Experiment.material_id == Material.id)
        .where(
            SmokeMeasurement.variable == "obscuration_drop_median",
            SmokeMeasurement.record_kind == "derived",
        )
        .order_by(Material.name, Experiment.test_label, SmokeMeasurement.id)
        .limit(200)
    )
    points = []
    for measurement, experiment, material in db.execute(statement):
        material_name = material.name if material else "material unspecified"
        points.append((f"{material_name} · test {experiment.test_label}", measurement.value_original))
    return _chart(
        points,
        unit="V",
        source="SAME-R derived per-test obscuration-drop medians; each point is a test summary, not a raw sensor time series.",
    )
