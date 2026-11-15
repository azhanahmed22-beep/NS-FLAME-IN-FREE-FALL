from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.models import (
    CombustionMeasurement, DatasetVersion, Experiment, ExperimentalCondition, IngestionIssue, NasaSource, SmokeMeasurement,
)
from app.services.ingestion.pipeline import ingest_file, seed_investigations, sha256_of
from tests.conftest import SYNTH_117, SYNTH_DETECT, SYNTH_TABLE

RAW_REAL = Path(__file__).resolve().parents[1] / "data" / "raw"


def run(session, path, parser, tmp_path, psi="PSI-TEST-1", derived=False):
    return ingest_file(session, path=path, psi_id=psi, parser_name=parser, is_derived=derived,
                       origin="synthetic_test", raw_dir=tmp_path / "raw")


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def test_raw_file_preserved_and_hashed(session, write, tmp_path):
    p = write("t.csv", SYNTH_TABLE)
    v = run(session, p, "same_r_table", tmp_path)
    src = session.get(NasaSource, v.source_id)
    assert sha256_of(Path(src.raw_path)) == sha256_of(p) == src.sha256
    assert src.is_derived is False


def test_provenance_on_every_record(session, write, tmp_path):
    run(session, write("t.csv", SYNTH_TABLE), "same_r_table", tmp_path)
    for model in (Experiment, ExperimentalCondition):
        for row in session.scalars(select(model)):
            assert row.dataset_version_id and row.source_file == "t.csv" and row.source_row >= 2
            assert row.record_kind in ("measured", "simulated", "derived")


def test_original_and_normalized_values_both_kept(session, write, tmp_path):
    run(session, write("t.csv", SYNTH_TABLE), "same_r_table", tmp_path)
    c = session.scalars(select(ExperimentalCondition).where(ExperimentalCondition.name == "inlet_velocity")).first()
    assert c.value_original == 5.0 and c.unit_original == "cm/s"
    assert c.value_normalized == pytest.approx(0.05) and c.unit_normalized == "m/s"


def test_parent_link_and_label_reuse(session, write, tmp_path):
    run(session, write("t.csv", SYNTH_TABLE), "same_r_table", tmp_path)
    child = session.scalar(select(Experiment).where(Experiment.test_label == "1a"))
    parent = session.get(Experiment, child.parent_experiment_id)
    assert parent.test_label == "1" and parent.material_id == child.material_id
    assert count(session, Experiment) == 4
    assert child.gravity_environment is None  # never inferred


def test_ingestion_is_idempotent(session, write, tmp_path):
    p = write("t.csv", SYNTH_TABLE)
    v1 = run(session, p, "same_r_table", tmp_path)
    n = count(session, Experiment)
    v2 = run(session, p, "same_r_table", tmp_path)
    assert v1.id == v2.id and count(session, Experiment) == n and count(session, DatasetVersion) == 1


def test_detection_links_and_logs_orphans(session, write, tmp_path):
    run(session, write("t.csv", SYNTH_TABLE), "same_r_table", tmp_path)
    run(session, write("d.csv", SYNTH_DETECT), "same_r_detection_by_test", tmp_path, derived=True)
    issue_codes = [i.code for i in session.scalars(select(IngestionIssue))]
    assert "orphan_test" in issue_codes          # test 77 does not exist
    assert "material_mismatch" in issue_codes    # test 1 exists, but not for MatC
    linked = session.scalars(select(SmokeMeasurement).where(SmokeMeasurement.experiment_id.is_not(None))).all()
    assert linked and all(s.record_kind == "derived" for s in linked)
    unlinked = session.scalars(select(SmokeMeasurement).where(SmokeMeasurement.experiment_id.is_(None))).all()
    assert unlinked and all("unlinked_test=" in s.qualifier for s in unlinked)


def test_psi117_model_and_experiment_kept_apart(session, write, tmp_path):
    run(session, write("p.csv", SYNTH_117), "psi117_extinction_tidy", tmp_path, psi="PSI-TEST-2", derived=True)
    kinds = {c.record_kind for c in session.scalars(select(CombustionMeasurement))}
    assert kinds == {"measured", "simulated"}
    assert session.scalar(select(func.count()).select_from(IngestionIssue).where(IngestionIssue.code == "exact_duplicate_row")) == 1


def test_failed_ingestion_is_logged_not_raised(session, write, tmp_path):
    v = run(session, write("bad.csv", "x,y\n1,2\n"), "same_r_table", tmp_path)
    assert v.status == "failed"
    issue = session.scalar(select(IngestionIssue).where(IngestionIssue.dataset_version_id == v.id))
    assert issue.severity == "error" and "missing expected columns" in issue.message
    assert count(session, Experiment) == 0


def test_unknown_investigation_rejected(session, write, tmp_path):
    with pytest.raises(ValueError, match="not seeded"):
        run(session, write("t.csv", SYNTH_TABLE), "same_r_table", tmp_path, psi="PSI-NOPE")


@pytest.mark.skipif(not (RAW_REAL / "PSI-101_Experimental_table_SAME-R.csv").exists(), reason="user-supplied CSVs not present")
def test_user_supplied_files_end_to_end(session, tmp_path):
    import json
    manifest = json.loads((RAW_REAL.parent / "manifest.json").read_text())
    seed_investigations(session, manifest["investigations"])
    for d in manifest["datasets"]:
        v = ingest_file(session, path=RAW_REAL / d["file"], psi_id=d["psi_id"], parser_name=d["parser"],
                        is_derived=d["is_derived"], origin=d["origin"], raw_dir=tmp_path / "raw")
        assert v.status == "completed", d["file"]
    assert count(session, Experiment) == 109 + 89            # SAME-R table + PSI-117 (4 duplicates excluded)
    codes = [i.code for i in session.scalars(select(IngestionIssue))]
    assert "orphan_test" not in codes and "material_mismatch" not in codes  # all 45 detection tests link
    assert codes.count("exact_duplicate_row") == 4
    assert codes.count("duplicate_test_label") == 0          # test 57 exists under two materials, correctly kept
    assert count(session, SmokeMeasurement) == 405 + 30 + 220
