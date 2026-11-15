import pytest

from app.services.processing.units import normalize


@pytest.mark.parametrize("value,unit,expected,target", [
    (8.1, "cm/s", 0.081, "m/s"), (60, "sec", 60, "s"), (1.0, "atm", 101325.0, "Pa"),
    (2.0, "mm2/s", 2e-6, "m2/s"), (3.3, "V", 3.3, "V"), (1.38, "", 1.38, "1"),
])
def test_known_units(value, unit, expected, target):
    out, unit_out = normalize(value, unit)
    assert out == pytest.approx(expected)
    assert unit_out == target


def test_unknown_unit_is_not_guessed():
    assert normalize(5.0, "furlongs/fortnight") == (None, None)


def test_missing_value_or_unit():
    assert normalize(None, "s") == (None, None)
    assert normalize(5.0, None) == (None, None)
