"""test_table_merge.py — Tests for report table merging."""
from src.domain.indicator.entities import IndicatorSeries
from src.domain.report.table_merge import merge_series


def test_merge_empty():
    assert merge_series([]) == []


def test_merge_single_series():
    series = IndicatorSeries("IND1", "USA", {"2000": "10", "2001": "20"}, {})
    result = merge_series([series])
    
    assert len(result) == 2
    assert result[0] == {"year": "2000", "IND1": "10"}
    assert result[1] == {"year": "2001", "IND1": "20"}


def test_merge_multiple_series_outer_join():
    series1 = IndicatorSeries("IND1", "USA", {"2000": "10", "2001": "20"}, {})
    series2 = IndicatorSeries("IND2", "USA", {"2001": "30", "2002": "40"}, {})
    
    result = merge_series([series1, series2])
    
    assert len(result) == 3
    assert result[0] == {"year": "2000", "IND1": "10", "IND2": None}
    assert result[1] == {"year": "2001", "IND1": "20", "IND2": "30"}
    assert result[2] == {"year": "2002", "IND1": None, "IND2": "40"}
