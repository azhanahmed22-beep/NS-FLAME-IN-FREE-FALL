from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Experiment, Fuel, Investigation, Material

router = APIRouter(tags=["research"])


@router.get("/investigations")
def list_investigations(db: Session = Depends(get_db)) -> list[dict]:
    records = db.scalars(select(Investigation).order_by(Investigation.psi_id)).all()
    return [
        {
            "id": record.id,
            "psi_id": record.psi_id,
            "acronym": record.acronym,
            "title": record.title,
            "research_area": record.research_area,
            "doi": record.doi,
            "page_url": record.page_url,
            "availability_status": record.availability_status,
        }
        for record in records
    ]


@router.get("/experiments")
def list_experiments(db: Session = Depends(get_db)) -> list[dict]:
    statement = (
        select(Experiment, Investigation, Material, Fuel)
        .join(Investigation, Experiment.investigation_id == Investigation.id)
        .outerjoin(Material, Experiment.material_id == Material.id)
        .outerjoin(Fuel, Experiment.fuel_id == Fuel.id)
        .order_by(Investigation.psi_id, Experiment.test_label, Experiment.id)
    )
    return [
        {
            "id": experiment.id,
            "psi_id": investigation.psi_id,
            "investigation": investigation.acronym or investigation.title,
            "test_label": experiment.test_label,
            "material": material.name if material else None,
            "fuel": fuel.name if fuel else None,
            "description": experiment.description,
            "date_text": experiment.date_text,
            "gravity_environment": experiment.gravity_environment,
            "record_kind": experiment.record_kind,
            "source_file": experiment.source_file,
            "source_row": experiment.source_row,
        }
        for experiment, investigation, material, fuel in db.execute(statement)
    ]


@router.get("/materials")
def list_materials(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {"id": material.id, "name": material.name, "category": material.category}
        for material in db.scalars(select(Material).order_by(Material.name)).all()
    ]
