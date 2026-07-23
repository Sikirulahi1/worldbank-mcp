"""series_builder.py — Builds clean IndicatorSeries from observations."""
from src.domain.indicator.entities import IndicatorSeries, Observation
from src.domain.shaping.field_analysis import analyze_fields


def build_series(
    country_code: str, 
    indicator_code: str, 
    start_year: int, 
    end_year: int, 
    observations: list[Observation]
) -> IndicatorSeries:
    if not observations:
        data = {str(year): None for year in range(start_year, end_year + 1)}
        return IndicatorSeries(indicator=indicator_code, country=country_code, data=data, metadata={})
        
    constant_fields, _ = analyze_fields(observations)
    
    data = {str(year): None for year in range(start_year, end_year + 1)}
    
    for obs in observations:
        if obs.time_period and obs.time_period in data:
            data[obs.time_period] = obs.obs_value
            
    return IndicatorSeries(
        indicator=indicator_code,
        country=country_code,
        data=data,
        metadata=constant_fields
    )
