from datetime import datetime

from pydantic import BaseModel


class DatasetResponse(BaseModel):
    id: int
    source_id: int
    investigation_id: int
    psi_id: str
    investigation_acronym: str | None
    investigation_title: str | None
    filename: str
    sha256: str
    size_bytes: int
    origin: str
    is_derived: bool
    doi: str | None
    url: str | None
    parser_name: str
    parser_version: str
    status: str
    rows_read: int | None
    records_stored: int | None
    finished_at: datetime | None
    created_at: datetime
    issue_count: int
