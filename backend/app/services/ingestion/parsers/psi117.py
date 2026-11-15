"""PSI-117 tidy extinction table. 'experiment' rows are measured, 'model' rows
are simulated; they are never merged. Exact duplicate rows are excluded and logged."""
from pathlib import Path

import pandas as pd

from app.services.ingestion.types import ExperimentRecord, Issue, ParseResult, ValueRecord
from app.services.processing.quality import clean, exact_duplicate_mask, null_counts

_KIND = {"experiment": "measured", "model": "simulated"}
_REQUIRED = ["source_file", "fuel", "pressure_atm", "dext_cool", "dext_hot", "kb_mm2_s", "value_type"]


class Psi117ExtinctionParser:
    name = "psi117_extinction_tidy"
    version = "1"

    def parse(self, path: Path) -> ParseResult:
        df = pd.read_csv(path)
        missing = [c for c in _REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"{self.name}: missing expected columns {missing}")
        result = ParseResult(rows_read=len(df))
        for col, n in null_counts(df[["dext_cool", "dext_hot", "kb_mm2_s"]]).items():
            result.issues.append(Issue("info", "missing_values", f"{n} of {len(df)} rows have no value; left NULL.", column=col))
        result.issues.append(Issue("info", "unit_not_specified", "Extinction diameter columns (dext_*) carry no unit in the file; unit left NULL."))
        dup = exact_duplicate_mask(df)
        for idx in df.index[dup]:
            result.issues.append(Issue("warning", "exact_duplicate_row",
                                       "Identical to an earlier row; excluded. (Could be a true replicate - check upstream file.)", idx + 2))
        for idx, row in df[~dup].iterrows():
            line = idx + 2
            vtype = clean(row["value_type"])
            kind = _KIND.get(vtype or "")
            if kind is None:
                result.issues.append(Issue("error", "unknown_value_type", f"value_type {vtype!r} not recognised; skipped.", line, "value_type"))
                continue
            upstream = clean(row["source_file"])
            exp = ExperimentRecord(test_label=f"{upstream}:L{line}", record_kind=kind, source_row=line,
                                   fuel=clean(row["fuel"]), upstream_file=upstream)
            p = clean(row["pressure_atm"])
            if p is not None:
                exp.conditions.append(ValueRecord("pressure", float(p), "atm", kind, line, name_original="pressure_atm", upstream_file=upstream))
            for col, name, unit in (("dext_cool", "extinction_diameter_cool", None), ("dext_hot", "extinction_diameter_hot", None),
                                    ("kb_mm2_s", "kb", "mm2/s")):
                val = clean(row[col])
                if val is not None:
                    exp.combustion.append(ValueRecord(name, float(val), unit, kind, line, name_original=col, upstream_file=upstream))
            result.experiments.append(exp)
        return result
