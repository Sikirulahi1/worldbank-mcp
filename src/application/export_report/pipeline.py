"""pipeline.py — Export Report pipeline."""
from src.application.export_report.dto import ExportReportRequest
from src.application.get_country_indicator.dto import GetCountryIndicatorRequest
from src.application.get_country_indicator.pipeline import GetCountryIndicatorPipeline
from src.application.ports.data_port import IDataPort
from src.application.ports.file_port import IFileWriter
from src.application.ports.search_port import ISearchPort
from src.core.constants import SUPPORTED_EXPORT_FORMATS
from src.core.exceptions import UnsupportedFormatError
from src.core.result import ClarificationNeeded, DataResult, NotFound
from src.domain.indicator.entities import IndicatorSeries
from src.domain.report.table_merge import merge_series


class ExportReportPipeline:
    """Pipeline for fetching and exporting multiple indicators."""
    
    def __init__(self, search_port: ISearchPort, data_port: IDataPort, writers: dict[str, IFileWriter]):
        self._search_port = search_port
        self._data_port = data_port
        self._writers = writers
        self._country_indicator_pipeline = GetCountryIndicatorPipeline(search_port, data_port)

    async def execute(self, request: ExportReportRequest) -> str | ClarificationNeeded | NotFound:
        """Execute the export report pipeline and return the file path or outcome."""
        fmt = request.format.lower().strip()
        if fmt not in SUPPORTED_EXPORT_FORMATS or fmt not in self._writers:
            raise UnsupportedFormatError(f"Format '{fmt}' is not supported. Supported formats: {SUPPORTED_EXPORT_FORMATS}")
            
        writer = self._writers[fmt]
        
        resolved_series: list[IndicatorSeries] = []
        clarifications_needed: list[ClarificationNeeded] = []
        not_founds: list[NotFound] = []
        
        for topic in request.indicator_topics:
            ci_req = GetCountryIndicatorRequest(
                country_name=request.country_name,
                indicator_topic=topic,
                start_year=request.start_year,
                end_year=request.end_year,
                dimensions=request.dimensions
            )
            result = await self._country_indicator_pipeline.execute(ci_req)
            
            if isinstance(result, DataResult):
                resolved_series.append(result.series)
            elif isinstance(result, ClarificationNeeded):
                clarifications_needed.append(result)
            elif isinstance(result, NotFound):
                not_founds.append(result)
                
        if len(resolved_series) == 0:
            if clarifications_needed:
                return ClarificationNeeded(
                    candidates=[c for cn in clarifications_needed for c in cn.candidates],
                    context="All requested indicators failed. Some require clarification:\n" + "\n".join(cn.context for cn in clarifications_needed)
                )
            else:
                return NotFound(reason="All requested indicators failed to resolve.")
                
        if clarifications_needed or not_founds:
            failures = []
            for cn in clarifications_needed:
                failures.append(cn.context)
            for nf in not_founds:
                failures.append(nf.reason)
                
            combined_reason = "Partial failure during export. The following indicators could not be resolved cleanly:\n" + "\n".join(failures)
            
            if clarifications_needed:
                return ClarificationNeeded(
                    candidates=[c for cn in clarifications_needed for c in cn.candidates],
                    context=combined_reason
                )
            return NotFound(reason=combined_reason)
            
        rows = merge_series(resolved_series)
        
        file_path = await writer.write(rows, request.destination)
        
        return file_path
