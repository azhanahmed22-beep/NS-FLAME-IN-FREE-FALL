"""Unit normalization to SI. Original values are always kept by the caller;
a unit with no rule yields (None, None) instead of a guess."""
_RULES: dict[str, tuple[float, str]] = {
    "s": (1.0, "s"),
    "sec": (1.0, "s"),
    "cm/s": (0.01, "m/s"),
    "mm2/s": (1e-6, "m2/s"),
    "atm": (101325.0, "Pa"),
    "v": (1.0, "V"),
    "%": (1.0, "%"),
    "": (1.0, "1"),  # dimensionless
}


def normalize(value: float | None, unit: str | None) -> tuple[float | None, str | None]:
    if value is None or unit is None:
        return None, None
    rule = _RULES.get(unit.strip().lower())
    if rule is None:
        return None, None
    factor, target = rule
    return value * factor, target


def has_rule(unit: str | None) -> bool:
    return unit is not None and unit.strip().lower() in _RULES
