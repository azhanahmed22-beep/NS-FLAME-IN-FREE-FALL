from fastapi.testclient import TestClient

from app.api.v1 import ai
from app.database.session import get_db
from app.main import create_app
from app.models import (
    CombustionMeasurement,
    DatasetVersion,
    Experiment,
    Investigation,
    Material,
    NasaSource,
    SmokeMeasurement,
)


def test_workspace_endpoints_use_ingested_records(session, monkeypatch):
    investigation = session.query(Investigation).filter_by(psi_id="PSI-TEST-1").one()
    source = NasaSource(
        investigation_id=investigation.id,
        filename="derived-test.csv",
        sha256="c" * 64,
        size_bytes=256,
        origin="user_supplied",
        is_derived=True,
        raw_path="local-only.csv",
    )
    session.add(source)
    session.flush()
    version = DatasetVersion(
        source_id=source.id,
        parser_name="workspace_test",
        parser_version="1",
        status="completed",
        rows_read=2,
        records_stored=5,
    )
    session.add(version)
    materials = [Material(name="Kapton"), Material(name="Silicone")]
    session.add_all(materials)
    session.flush()

    for label, material, value in (
        ("test-1", materials[0], 0.1),
        ("test-2", materials[1], 0.2),
    ):
        experiment = Experiment(
            dataset_version_id=version.id,
            source_file=source.filename,
            source_row=2,
            record_kind="measured",
            investigation_id=investigation.id,
            test_label=label,
            material_id=material.id,
        )
        session.add(experiment)
        session.flush()
        session.add(
            SmokeMeasurement(
                dataset_version_id=version.id,
                source_file=source.filename,
                source_row=2,
                record_kind="derived",
                variable="obscuration_drop_median",
                value_original=value,
                unit_original="V",
                experiment_id=experiment.id,
            )
        )

    session.add_all(
        [
            SmokeMeasurement(
                dataset_version_id=version.id,
                source_file=source.filename,
                source_row=3,
                record_kind="derived",
                variable="NumDen",
                statistic="mean",
                qualifier="case=10cm;gravity=Earth;regime=earth",
                value_original=1.5,
            ),
            SmokeMeasurement(
                dataset_version_id=version.id,
                source_file=source.filename,
                source_row=4,
                record_kind="derived",
                variable="NumDen",
                statistic="mean",
                qualifier="case=10cm;gravity=Microgravity;regime=microgravity",
                value_original=2.5,
            ),
            CombustionMeasurement(
                dataset_version_id=version.id,
                source_file=source.filename,
                source_row=5,
                record_kind="measured",
                variable="extinction_diameter_cool",
                value_original=1.25,
            ),
        ]
    )
    session.commit()

    monkeypatch.setattr(ai, "_gemini_answer", lambda context: (None, None))
    app = create_app()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)

    expected_gets = (
        "/api/v1/investigations",
        "/api/v1/experiments",
        "/api/v1/materials",
        "/api/v1/datasets",
        "/api/v1/analytics/combustion",
        "/api/v1/analytics/materials",
        "/api/v1/analytics/microgravity",
        "/api/v1/analytics/overview",
        "/api/v1/analytics/smoke",
    )
    for path in expected_gets:
        response = client.get(path)
        assert response.status_code == 200, (path, response.text)

    assert len(client.get("/api/v1/analytics/smoke").json()["points"]) == 2
    assert len(client.get("/api/v1/analytics/microgravity").json()["points"]) == 2
    assert client.get("/api/v1/analytics/combustion").json()["points"][0]["value"] == 1.25
    comparison = client.post(
        "/api/v1/ranking/materials",
        json={"materials": ["Kapton", "Silicone"]},
    )
    assert comparison.status_code == 200
    assert [row["test_summaries"] for row in comparison.json()["results"]] == [1, 1]

    for operation in ("analyze", "compare", "research-summary"):
        response = client.post(
            f"/api/v1/ai/{operation}",
            json={"question": "Compare the available smoke records."},
        )
        assert response.status_code == 200
        assert response.json()["provider"] == "local-evidence"

    openapi = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/ai/analyze" in openapi
    assert "/api/v1/ai/compare" in openapi
    assert "/api/v1/ai/research-summary" in openapi
