"""Parsers for SAME-R (PSI-101) files: the experiment table and the derived
smoke-detector summaries. Line numbers: header = line 1, first data row = 2."""
import re
from pathlib import Path

import pandas as pd

from app.services.ingestion.types import ExperimentRecord, Issue, ParseResult, ValueRecord
from app.services.processing.quality import clean, null_counts

_CHILD = re.compile(r"^(\d+)([a-z])$")

_TABLE_CONDITIONS = {
    "Inlet velocity (cm/s)": ("inlet_velocity", "cm/s"),
    "Rt/R0": ("rt_over_r0", ""),
    "Duration (sec)": ("duration", "sec"),
    "Primary aging time (sec)": ("primary_aging_time", "sec"),
    "Primary mixing time (sec)": ("primary_mixing_time", "sec"),
    "Net aging time (sec)": ("net_aging_time", "sec"),
}
_TABLE_REQUIRED = ["Sample Type", "SAME Test #", *_TABLE_CONDITIONS]


def _require(df: pd.DataFrame, cols: list[str], name: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name}: missing expected columns {missing}")


class SameRTableParser:
    name = "same_r_table"
    version = "1"

    def parse(self, path: Path) -> ParseResult:
        df = pd.read_csv(path, dtype={"SAME Test #": str})
        df.columns = [c.strip() for c in df.columns]
        _require(df, _TABLE_REQUIRED, self.name)
        result = ParseResult(rows_read=len(df))
        for col, n in null_counts(df[list(_TABLE_CONDITIONS)]).items():
            result.issues.append(Issue("info", "missing_values", f"{n} of {len(df)} rows have no value; left NULL, not imputed.", column=col))

        labels = {(clean(r["Sample Type"]), clean(r["SAME Test #"])) for _, r in df.iterrows()}
        seen: set[tuple[str | None, str | None]] = set()
        for idx, row in df.iterrows():
            line = idx + 2
            material, label = clean(row["Sample Type"]), clean(row["SAME Test #"])
            if label is None:
                result.issues.append(Issue("error", "missing_test_label", "Row has no test number; skipped.", line, "SAME Test #"))
                continue
            if (material, label) in seen:
                result.issues.append(Issue("warning", "duplicate_test_label", f"Test {label} ({material}) repeated; later row skipped.", line, "SAME Test #"))
                continue
            seen.add((material, label))
            parent = None
            m = _CHILD.match(label)
            if m:
                parent = m.group(1)
                if (material, parent) not in labels:
                    result.issues.append(Issue("warning", "orphan_child_test", f"{label} has no parent test {parent} for {material}.", line))
                    parent = None
            exp = ExperimentRecord(
                test_label=label, record_kind="measured", source_row=line, material=material,
                parent_label=parent, description=clean(row.get("Description")), date_text=clean(row.get("Date")),
            )
            for col, (name, unit) in _TABLE_CONDITIONS.items():
                val = clean(row[col])
                if val is not None:
                    exp.conditions.append(ValueRecord(name, float(val), unit, "measured", line, name_original=col))
            result.experiments.append(exp)
        return result


_DETECTION = {
    "baseline_obsc_med_V": ("baseline_obscuration_median", "V"),
    "smoke_window_obsc_med_V": ("smoke_window_obscuration_median", "V"),
    "obsc_drop_med_V": ("obscuration_drop_median", "V"),
    "pct_window_below_3.30V": ("pct_window_below_3p30V", "%"),
    "smoke_window_scat_med_V": ("smoke_window_scattering_median", "V"),
    "smoke_window_ionA_med_V": ("smoke_window_ionization_median", "V"),
    "ionA_max_V": ("ionization_max", "V"),
    "n_samples": ("n_samples", ""),
    "duration_s": ("record_duration", "s"),
}


class SameRDetectionByTestParser:
    """Per-test detector statistics. This file is a derived summary, so values are 'derived'."""

    name = "same_r_detection_by_test"
    version = "1"

    def parse(self, path: Path) -> ParseResult:
        df = pd.read_csv(path, dtype={"test_no": str})
        _require(df, ["test_no", "material", *_DETECTION], self.name)
        result = ParseResult(rows_read=len(df))
        for idx, row in df.iterrows():
            line = idx + 2
            exp = ExperimentRecord(test_label=clean(row["test_no"]), record_kind="derived", source_row=line,
                                   material=clean(row["material"]), attach_only=True)
            for col, (name, unit) in _DETECTION.items():
                val = clean(row[col])
                if val is not None:
                    exp.smoke.append(ValueRecord(name, float(val), unit, "derived", line, statistic=None, name_original=col))
            result.experiments.append(exp)
        return result


_BY_MATERIAL = {
    "tests": ("test_count", ""), "obsc_drop_med_V": ("obscuration_drop_median", "V"),
    "obsc_drop_min_V": ("obscuration_drop_min", "V"), "obsc_drop_max_V": ("obscuration_drop_max", "V"),
    "pct_below_3p30_med": ("pct_below_3p30V_median", "%"), "ionA_med_V": ("ionization_median", "V"),
}


class SameRDetectionByMaterialParser:
    """Per-material rollup. Aggregates are tagged so later stages can exclude them from training."""

    name = "same_r_detection_by_material"
    version = "1"

    def parse(self, path: Path) -> ParseResult:
        df = pd.read_csv(path)
        _require(df, ["material", *_BY_MATERIAL], self.name)
        result = ParseResult(rows_read=len(df))
        for idx, row in df.iterrows():
            line = idx + 2
            for col, (name, unit) in _BY_MATERIAL.items():
                val = clean(row[col])
                if val is not None:
                    result.loose_smoke.append(ValueRecord(name, float(val), unit, "derived", line,
                                                          qualifier=f"aggregate=material;material={clean(row['material'])}", name_original=col))
        return result
