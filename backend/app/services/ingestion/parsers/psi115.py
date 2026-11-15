"""PSI-115 per-file summary statistics (derived). One loose smoke record per
(file, variable, statistic). Gravity labels are kept verbatim."""
from pathlib import Path

import pandas as pd

from app.services.ingestion.types import Issue, ParseResult, ValueRecord
from app.services.processing.quality import clean, null_counts

# Case-only variants of the same variable name seen in the file.
_VARIABLE_CANON = {"numden": "NumDen", "u": "U", "v": "V"}
_STATS = ["n_values", "min", "max", "mean", "pct_above_zero"]
_REQUIRED = ["file", "case", "gravity", "variable", *_STATS]


def _regime(label: str | None) -> str | None:
    """Coarse regime taken from the label prefix only; other labels stay unclassified."""
    if label is None:
        return None
    low = label.lower()
    if low.startswith("microgravity"):
        return "microgravity"
    if low.startswith("earth"):
        return "earth"
    return None


class Psi115SummaryParser:
    name = "psi115_summary"
    version = "1"

    def parse(self, path: Path) -> ParseResult:
        df = pd.read_csv(path)
        missing = [c for c in _REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"{self.name}: missing expected columns {missing}")
        result = ParseResult(rows_read=len(df))
        for col, n in null_counts(df[["case", "gravity"]]).items():
            result.issues.append(Issue("warning", "missing_label", f"{n} rows have no '{col}' label; kept unlabelled, not guessed.", column=col))
        result.issues.append(Issue("info", "unit_not_specified", "The summary file gives no units for min/max/mean; unit left NULL."))
        for idx, row in df.iterrows():
            line = idx + 2
            var_orig = clean(row["variable"])
            var = _VARIABLE_CANON.get(var_orig.lower(), var_orig) if var_orig else None
            if var is None:
                result.issues.append(Issue("error", "missing_variable", "Row has no variable name; skipped.", line, "variable"))
                continue
            case, grav = clean(row["case"]), clean(row["gravity"])
            qualifier = f"case={case};gravity={grav};regime={_regime(grav)}"
            for stat in _STATS:
                val = clean(row[stat])
                if val is None:
                    continue
                unit = "" if stat in ("n_values",) else ("%" if stat == "pct_above_zero" else None)
                result.loose_smoke.append(ValueRecord(var, float(val), unit, "derived", line, statistic=stat,
                                                      qualifier=qualifier, name_original=var_orig, upstream_file=clean(row["file"])))
        return result
