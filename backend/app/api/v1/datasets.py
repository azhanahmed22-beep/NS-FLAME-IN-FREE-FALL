from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import DatasetVersion, IngestionIssue, Investigation, NasaSource
from app.schemas.datasets import DatasetResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetResponse])
def list_datasets(
    status: Literal["processing", "completed", "failed"] | None = None,
    psi_id: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[DatasetResponse]:
    issue_counts = (
        select(
            IngestionIssue.dataset_version_id.label("dataset_version_id"),
            func.count(IngestionIssue.id).label("issue_count"),
        )
        .group_by(IngestionIssue.dataset_version_id)
        .subquery()
    )
    statement = (
        select(
            DatasetVersion,
            NasaSource,
            Investigation,
            func.coalesce(issue_counts.c.issue_count, 0),
        )
        .join(NasaSource, DatasetVersion.source_id == NasaSource.id)
        .join(Investigation, NasaSource.investigation_id == Investigation.id)
        .outerjoin(issue_counts, issue_counts.c.dataset_version_id == DatasetVersion.id)
        .order_by(DatasetVersion.created_at.desc(), DatasetVersion.id.desc())
        .offset(offset)
        .limit(limit)
    )
    if status is not None:
        statement = statement.where(DatasetVersion.status == status)
    if psi_id is not None:
        statement = statement.where(Investigation.psi_id == psi_id)

    records = db.execute(statement)
    return [
        DatasetResponse(
            id=version.id,
            source_id=source.id,
            investigation_id=investigation.id,
            psi_id=investigation.psi_id,
            investigation_acronym=investigation.acronym,
            investigation_title=investigation.title,
            filename=source.filename,
            sha256=source.sha256,
            size_bytes=source.size_bytes,
            origin=source.origin,
            is_derived=source.is_derived,
            doi=source.doi,
            url=source.url,
            parser_name=version.parser_name,
            parser_version=version.parser_version,
            status=version.status,
            rows_read=version.rows_read,
            records_stored=version.records_stored,
            finished_at=version.finished_at,
            created_at=version.created_at,
            issue_count=issue_count,
        )
        for version, source, investigation, issue_count in records
    ]
