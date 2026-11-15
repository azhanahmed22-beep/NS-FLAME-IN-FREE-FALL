import pytest

from app.services.ingestion.parsers.psi115 import Psi115SummaryParser
from app.services.ingestion.parsers.psi117 import Psi117ExtinctionParser
from app.services.ingestion.parsers.same_r import SameRDetectionByTestParser, SameRTableParser
from tests.conftest import SYNTH_115, SYNTH_117, SYNTH_DETECT, SYNTH_TABLE


def codes(result):
    return [i.code for i in result.issues]


def test_table_parent_child_and_label_reuse_across_materials(write):
    r = SameRTableParser().parse(write("t.csv", SYNTH_TABLE))
    by = {(e.material, e.test_label): e for e in r.experiments}
    assert by[("MatA", "1a")].parent_label == "1"
    assert ("MatB", "1") in by and ("MatA", "1") in by  # same label, different material
    assert by[("MatB", "9a")].parent_label is None
    assert "orphan_child_test" in codes(r)
    assert "duplicate_test_label" in codes(r)
    assert len(r.experiments) == 4  # the repeated MatB/1 row is skipped


def test_table_missing_values_stay_null(write):
    r = SameRTableParser().parse(write("t.csv", SYNTH_TABLE))
    child = next(e for e in r.experiments if e.test_label == "1a")
    names = {c.name for c in child.conditions}
    assert "duration" not in names and "net_aging_time" in names
    assert any(i.code == "missing_values" and i.column == "Duration (sec)" for i in r.issues)


def test_missing_columns_raise(write):
    with pytest.raises(ValueError, match="missing expected columns"):
        SameRTableParser().parse(write("bad.csv", "a,b\n1,2\n"))


def test_detection_is_derived_and_attach_only(write):
    r = SameRDetectionByTestParser().parse(write("d.csv", SYNTH_DETECT))
    assert all(e.attach_only and e.record_kind == "derived" for e in r.experiments)
    assert all(v.record_kind == "derived" for e in r.experiments for v in e.smoke)


def test_psi117_duplicates_and_kinds(write):
    r = Psi117ExtinctionParser().parse(write("p.csv", SYNTH_117))
    assert codes(r).count("exact_duplicate_row") == 1
    assert "unknown_value_type" in codes(r)
    assert sorted(e.record_kind for e in r.experiments) == ["measured", "simulated"]
    assert all(c.unit is None for e in r.experiments for c in e.combustion if c.name.startswith("extinction"))


def test_psi115_variable_canonicalisation_and_missing_labels(write):
    r = Psi115SummaryParser().parse(write("s.csv", SYNTH_115))
    assert {v.name for v in r.loose_smoke} == {"NumDen", "U"}
    assert next(v for v in r.loose_smoke if v.name == "NumDen").name_original == "Numden"
    assert "missing_label" in codes(r)
    assert any("regime=earth" in (v.qualifier or "") for v in r.loose_smoke)
