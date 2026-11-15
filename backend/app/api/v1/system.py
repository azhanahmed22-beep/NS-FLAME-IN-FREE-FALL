from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import DatasetVersion, Investigation, IngestionIssue

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
def system_status(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {
        "database": "ok",
        "investigations": db.scalar(select(func.count()).select_from(Investigation)),
        "dataset_versions": {
            s: db.scalar(select(func.count()).select_from(DatasetVersion).where(DatasetVersion.status == s))
            for s in ("completed", "failed", "processing")
        },
        "ingestion_issues": db.scalar(select(func.count()).select_from(IngestionIssue)),
    }
