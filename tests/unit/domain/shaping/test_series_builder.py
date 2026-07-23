"""test_series_builder.py — Tests for series_builder."""
from src.domain.indicator.entities import Observation
from src.domain.shaping.series_builder import build_series


def test_build_series_empty():
    series = build_series("USA", "IND1", 2020, 2021, [])
    assert series.country == "USA"
    assert series.indicator == "IND1"
    assert series.data == {"2020": None, "2021": None}
    assert not series.metadata


def test_build_series_clean():
    obs = [
        Observation(indicator="GDP", ref_area="NGA", time_period="2020", obs_value="21.06", raw_fields={"FREQ": "A"}),
        Observation(indicator="GDP", ref_area="NGA", time_period="2021", obs_value="23.32", raw_fields={"FREQ": "A"}),
    ]
    
    series = build_series("NGA", "GDP", 2020, 2021, obs)
    
    assert series.country == "NGA"
    assert series.indicator == "GDP"
    assert series.data == {"2020": "21.06", "2021": "23.32"}
    assert series.metadata == {"FREQ": "A"}


def test_build_series_with_missing_years():
    obs = [
        Observation(indicator="GDP", ref_area="NGA", time_period="2020", obs_value="21.06", raw_fields={"FREQ": "A"}),
        # 2021 is missing
        Observation(indicator="GDP", ref_area="NGA", time_period="2022", obs_value="24.12", raw_fields={"FREQ": "A"}),
    ]
    
    series = build_series("NGA", "GDP", 2020, 2022, obs)
    
    assert series.country == "NGA"
    assert series.indicator == "GDP"
    assert series.data == {"2020": "21.06", "2021": None, "2022": "24.12"}
    assert series.metadata == {"FREQ": "A"}
