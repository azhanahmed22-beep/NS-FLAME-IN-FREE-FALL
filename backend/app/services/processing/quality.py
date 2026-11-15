"""Data-quality helpers used by parsers."""
import math

import pandas as pd


def clean(value):
    """NaN/blank -> None, numpy scalars -> python scalars."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if hasattr(value, "item"):
        return value.item()
    return value


def null_counts(df: pd.DataFrame) -> dict[str, int]:
    counts = df.isna().sum()
    return {str(c): int(n) for c, n in counts.items() if n > 0}


def exact_duplicate_mask(df: pd.DataFrame) -> pd.Series:
    """True for every repeat after the first occurrence of an identical row."""
    return df.duplicated(keep="first")
