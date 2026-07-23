"""pipeline.py — Get Country Indicator pipeline."""
from src.application.get_country_indicator.dto import GetCountryIndicatorRequest
from src.application.get_indicator_data.dto import GetIndicatorDataRequest
from src.application.get_indicator_data.pipeline import GetIndicatorDataPipeline
from src.application.ports.data_port import IDataPort
from src.application.ports.search_port import ISearchPort
from src.application.search_indicator.dto import SearchIndicatorRequest
from src.application.search_indicator.pipeline import SearchIndicatorPipeline
from src.core.result import ClarificationNeeded, DataResult, NotFound
from src.domain.country.entities import Country
from src.domain.country.resolution import resolve_country
from src.domain.indicator.disambiguation import disambiguate_candidates
from src.domain.indicator.entities import IndicatorCandidate


class GetCountryIndicatorPipeline:
    """Pipeline for resolving country and indicator, and fetching data."""
    
    def __init__(self, search_port: ISearchPort, data_port: IDataPort):
        self._search_pipeline = SearchIndicatorPipeline(search_port)
        self._data_pipeline = GetIndicatorDataPipeline(data_port)

    async def execute(self, request: GetCountryIndicatorRequest) -> DataResult | ClarificationNeeded | NotFound:
        """Execute the country indicator fetching pipeline."""
        country_result = resolve_country(request.country_name)
        if isinstance(country_result, (ClarificationNeeded, NotFound)):
            return country_result
            
        country: Country = country_result
        
        search_req = SearchIndicatorRequest(topic=request.indicator_topic)
        search_result = await self._search_pipeline.execute(search_req)
        
        if isinstance(search_result, NotFound):
            return search_result
            
        candidates: list[IndicatorCandidate] = search_result
        
        disambiguate_result = disambiguate_candidates(candidates, query=request.indicator_topic)
        if isinstance(disambiguate_result, (ClarificationNeeded, NotFound)):
            return disambiguate_result
            
        indicator: IndicatorCandidate = disambiguate_result
        
        data_req = GetIndicatorDataRequest(
            indicator_code=indicator.idno,
            country_code=country.iso3,
            start_year=request.start_year,
            end_year=request.end_year,
            dimensions=request.dimensions
        )
        return await self._data_pipeline.execute(data_req)
