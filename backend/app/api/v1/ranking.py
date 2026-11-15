from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Experiment, Material, SmokeMeasurement
from app.schemas.workspace import MaterialComparisonRequest

router = APIRouter(prefix="/ranking", tags=["ranking"])


@router.post("/materials")
def compare_materials(
    request: MaterialComparisonRequest,
    db: Session = Depends(get_db),
) -> dict:
    names = list(dict.fromkeys(name.strip() for name in request.materials if name.strip()))
    if len(names) < 2:
        return {
            "method": "derived smoke evidence comparison",
            "unit": "V",
            "not_a_safety_rating": True,
            "results": [],
            "note": "Select at least two distinct material names.",
        }

    statement = (
        select(
            Material.name,
            func.count(SmokeMeasurement.id),
            func.avg(SmokeMeasurement.value_original),
        )
        .join(Experiment, Experiment.material_id == Material.id)
        .join(SmokeMeasurement, SmokeMeasurement.experiment_id == Experiment.id)
        .where(
            Material.name.in_(names),
            SmokeMeasurement.variable == "obscuration_drop_median",
            SmokeMeasurement.record_kind == "derived",
        )
        .group_by(Material.name)
    )
    evidence = {
        name: (int(count), float(mean) if mean is not None else None)
        for name, count, mean in db.execute(statement)
    }
    return {
        "method": "mean of available derived per-test obscuration-drop medians",
        "unit": "V",
        "not_a_safety_rating": True,
        "results": [
            {
                "material": name,
                "test_summaries": evidence.get(name, (0, None))[0],
                "mean_obscuration_drop": evidence.get(name, (0, None))[1],
            }
            for name in names
        ],
        "note": "Evidence coverage varies by material. This comparison is not a material-safety or flight-readiness assessment.",
    }
