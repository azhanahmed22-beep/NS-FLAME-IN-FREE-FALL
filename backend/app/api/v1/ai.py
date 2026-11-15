import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db
from app.models import (
    CombustionMeasurement,
    DatasetVersion,
    Investigation,
    NasaSource,
    SmokeMeasurement,
)
from app.schemas.workspace import ResearchQuestion

router = APIRouter(prefix="/ai", tags=["AI research assistant"])


def _evidence_context(db: Session, question: str) -> tuple[str, list[dict], dict[str, int]]:
    datasets = db.execute(
        select(
            Investigation.psi_id,
            NasaSource.filename,
            NasaSource.is_derived,
            DatasetVersion.status,
            DatasetVersion.records_stored,
        )
        .join(NasaSource, NasaSource.investigation_id == Investigation.id)
        .join(DatasetVersion, DatasetVersion.source_id == NasaSource.id)
        .order_by(Investigation.psi_id, NasaSource.filename)
    ).all()
    sources = [
        {
            "psi_id": psi_id,
            "filename": filename,
            "is_derived": is_derived,
            "status": status,
        }
        for psi_id, filename, is_derived, status, _ in datasets
    ]
    counts = {
        "completed_datasets": sum(status == "completed" for _, _, _, status, _ in datasets),
        "stored_records": sum(records or 0 for _, _, _, status, records in datasets if status == "completed"),
        "combustion_records": db.scalar(
            select(func.count()).select_from(CombustionMeasurement)
        ) or 0,
        "smoke_records": db.scalar(select(func.count()).select_from(SmokeMeasurement)) or 0,
    }

    lowered = question.lower()
    if any(
        word in lowered
        for word in ("smoke", "aerosol", "particle", "obscuration", "gravity", "numden")
    ):
        measurement_rows = db.execute(
            select(
                SmokeMeasurement.variable,
                SmokeMeasurement.value_original,
                SmokeMeasurement.unit_original,
                SmokeMeasurement.record_kind,
                SmokeMeasurement.source_file,
                SmokeMeasurement.source_row,
            )
            .order_by(SmokeMeasurement.id)
            .limit(20)
        ).all()
    else:
        measurement_rows = db.execute(
            select(
                CombustionMeasurement.variable,
                CombustionMeasurement.value_original,
                CombustionMeasurement.unit_original,
                CombustionMeasurement.record_kind,
                CombustionMeasurement.source_file,
                CombustionMeasurement.source_row,
            )
            .order_by(CombustionMeasurement.id)
            .limit(20)
        ).all()

    measurements = [
        {
            "variable": variable,
            "value": value,
            "unit": unit,
            "record_kind": record_kind,
            "source_file": source_file,
            "source_row": source_row,
        }
        for variable, value, unit, record_kind, source_file, source_row in measurement_rows
    ]
    context = (
        f"Question: {question}\n"
        f"Database counts: {counts}\n"
        f"Available dataset provenance: {sources}\n"
        f"Relevant stored records: {measurements}\n"
        "Answer only from this evidence. State when the data cannot answer the question. "
        "Distinguish measured, simulated, and derived records; include filenames and row numbers "
        "when useful. Never infer missing units, gravity, or safety conclusions."
    )
    return context, sources, counts


def _local_answer(counts: dict[str, int]) -> str:
    return (
        "Gemini is not configured, so no generative interpretation was made. "
        f"The local database reports {counts['completed_datasets']} completed datasets, "
        f"{counts['stored_records']} stored records, {counts['combustion_records']} combustion "
        f"records, and {counts['smoke_records']} smoke records. Use the attached dataset sources "
        "to inspect evidence; this summary is not a scientific or safety conclusion."
    )


def _gemini_answer(context: str) -> tuple[str | None, str | None]:
    settings = get_settings()
    if settings.gemini_api_key is None:
        return None, None

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    try:
        response = httpx.post(
            url,
            headers={"x-goog-api-key": settings.gemini_api_key.get_secret_value()},
            json={
                "contents": [{"parts": [{"text": context}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700},
            },
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        return None, f"Gemini returned HTTP {error.response.status_code}; showing local evidence summary."
    except httpx.RequestError:
        return None, "Gemini could not be reached; showing local evidence summary."

    try:
        data = response.json()
        parts = data["candidates"][0]["content"]["parts"]
        answer = "\n".join(part["text"] for part in parts if isinstance(part.get("text"), str)).strip()
    except (KeyError, IndexError, TypeError, ValueError):
        return None, "Gemini returned an unreadable response; showing local evidence summary."
    if not answer:
        return None, "Gemini returned no answer text; showing local evidence summary."
    return answer, None


def _answer_research_question(
    operation: str,
    request: ResearchQuestion,
    db: Session,
) -> dict:
    context, sources, counts = _evidence_context(db, request.question)
    answer, warning = _gemini_answer(context)
    provider = "gemini" if answer else "local-evidence"
    return {
        "provider": provider,
        "operation": operation,
        "answer": answer or _local_answer(counts),
        "sources": sources,
        "warning": warning,
    }


@router.post("/analyze")
def analyze(
    request: ResearchQuestion,
    db: Session = Depends(get_db),
) -> dict:
    return _answer_research_question("analyze", request, db)


@router.post("/compare")
def compare(
    request: ResearchQuestion,
    db: Session = Depends(get_db),
) -> dict:
    return _answer_research_question("compare", request, db)


@router.post("/research-summary")
def research_summary(
    request: ResearchQuestion,
    db: Session = Depends(get_db),
) -> dict:
    return _answer_research_question("research-summary", request, db)
