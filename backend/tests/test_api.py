from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import create_app
from app.models import DatasetVersion, IngestionIssue, Investigation, NasaSource


def test_health_and_status(session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    body = client.get("/api/v1/system/status").json()
    assert body["database"] == "ok" and body["investigations"] == 2
    assert body["dataset_versions"] == {"completed": 0, "failed": 0, "processing": 0}


def test_cors_allows_local_frontend_and_rejects_unconfigured_origin():
    client = TestClient(create_app())
    allowed = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    denied = client.options(
        "/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in denied.headers


def test_dataset_list_returns_ingested_provenance(session):
    investigation = session.query(Investigation).filter_by(psi_id="PSI-TEST-1").one()
    source = NasaSource(
        investigation_id=investigation.id,
        filename="sample.csv",
        sha256="b" * 64,
        size_bytes=128,
        origin="user_supplied",
        is_derived=True,
        doi="10.0000/example",
        url="https://example.test/source",
        raw_path="must-not-be-exposed.csv",
    )
    session.add(source)
    session.flush()
    version = DatasetVersion(
        source_id=source.id,
        parser_name="sample_parser",
        parser_version="1",
        status="completed",
        rows_read=4,
        records_stored=3,
    )
    session.add(version)
    session.flush()
    session.add(
        IngestionIssue(
            dataset_version_id=version.id,
            severity="warning",
            code="missing_unit",
            message="Unit was not included in the source.",
        )
    )
    session.commit()

    app = create_app()
    app.dependency_overrides[get_db] = lambda: session
    response = TestClient(app).get("/api/v1/datasets?status=completed&psi_id=PSI-TEST-1")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": version.id,
            "source_id": source.id,
            "investigation_id": investigation.id,
            "psi_id": "PSI-TEST-1",
            "investigation_acronym": "SYNTH",
            "investigation_title": None,
            "filename": "sample.csv",
            "sha256": "b" * 64,
            "size_bytes": 128,
            "origin": "user_supplied",
            "is_derived": True,
            "doi": "10.0000/example",
            "url": "https://example.test/source",
            "parser_name": "sample_parser",
            "parser_version": "1",
            "status": "completed",
            "rows_read": 4,
            "records_stored": 3,
            "finished_at": None,
            "created_at": version.created_at.isoformat(),
            "issue_count": 1,
        }
    ]
    assert "raw_path" not in response.text
