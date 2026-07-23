"""test_field_analysis.py — Tests for field classification logic."""
from src.domain.indicator.entities import Observation
from src.domain.shaping.field_analysis import analyze_fields


def test_analyze_empty():
    const, var = analyze_fields([])
    assert not const
    assert not var


def test_analyze_single_row():
    obs = Observation("IND1", "USA", "2000", "100", {"UNIT": "USD", "SCALE": "Millions"})
    const, var = analyze_fields([obs])
    assert const == {"UNIT": "USD", "SCALE": "Millions"}
    assert not var


def test_analyze_multi_row_varying():
    obs1 = Observation("IND1", "USA", "2000", "100", {"UNIT": "USD", "SCALE": "Millions"})
    obs2 = Observation("IND1", "USA", "2001", "110", {"UNIT": "USD", "SCALE": "Billions"})
    const, var = analyze_fields([obs1, obs2])
    assert const == {"UNIT": "USD"}
    assert var == {"SCALE"}
