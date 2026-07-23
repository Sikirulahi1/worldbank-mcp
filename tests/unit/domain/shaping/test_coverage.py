"""test_coverage.py — Tests for data coverage analysis."""
from src.domain.shaping.coverage import analyze_coverage


def test_analyze_coverage_perfect():
    warnings = analyze_coverage(2000, 2002, 2000, 2002, {"2000": "1", "2001": "2", "2002": "3"})
    assert not warnings


def test_analyze_coverage_out_of_bounds():
    warnings = analyze_coverage(1999, 2003, 2000, 2002, {"2000": "1", "2001": "2", "2002": "3"})
    assert "Requested start 1999 is before data begins in 2000." in warnings
    assert "Requested end 2003 is after data ends in 2002." in warnings


def test_analyze_coverage_internal_gap():
    warnings = analyze_coverage(2000, 2003, 2000, 2003, {"2000": "1", "2001": None, "2003": "4"})
    assert "Missing data for year 2001." in warnings
    assert "Missing data for year 2002." in warnings
