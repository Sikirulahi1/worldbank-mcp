"""pipeline.py — Get Indicator Data pipeline."""
from src.application.get_indicator_data.dto import GetIndicatorDataRequest
from src.application.ports.data_port import IDataPort
from src.core.result import DataResult
from src.domain.indicator.validation import validate_country_code, validate_indicator_code, validate_year_range
from src.domain.shaping.coverage import analyze_coverage
from src.domain.shaping.series_builder import build_series


class GetIndicatorDataPipeline:
    """Pipeline for fetching, shaping, and validating indicator data."""
    
    def __init__(self, data_port: IDataPort):
        self._data_port = data_port

    async def execute(self, request: GetIndicatorDataRequest) -> DataResult:
        """Execute the data fetching pipeline."""
        validate_indicator_code(request.indicator_code)
        validate_country_code(request.country_code)
        validate_year_range(request.start_year, request.end_year)
        
        observations = await self._data_port.fetch(
            indicator_code=request.indicator_code,
            country_code=request.country_code,
            start_year=request.start_year,
            end_year=request.end_year,
            dimensions=request.dimensions
        )
        
        series = build_series(
            country_code=request.country_code, 
            indicator_code=request.indicator_code, 
            start_year=request.start_year, 
            end_year=request.end_year, 
            observations=observations
        )
        
        if not observations:
            warnings = [f"No data returned for indicator {request.indicator_code} in {request.country_code} ({request.start_year}-{request.end_year})."]
        else:
            years = [int(obs.time_period) for obs in observations if obs.time_period and obs.time_period.isdigit()]
            if years:
                warnings = analyze_coverage(request.start_year, request.end_year, min(years), max(years), series.data)
            else:
                warnings = ["Data returned but contained no valid years."]
                
        return DataResult(series=series, coverage_warnings=warnings)
