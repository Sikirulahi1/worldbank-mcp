"""tool_handlers.py — Thin glue: MCP tool call -> DTO -> pipeline -> MCP result."""
import json
from dataclasses import asdict

from mcp.types import TextContent

from src.application.export_report.dto import ExportReportRequest
from src.application.export_report.pipeline import ExportReportPipeline
from src.application.get_country_indicator.dto import GetCountryIndicatorRequest
from src.application.get_country_indicator.pipeline import GetCountryIndicatorPipeline
from src.application.get_indicator_data.dto import GetIndicatorDataRequest
from src.application.get_indicator_data.pipeline import GetIndicatorDataPipeline
from src.application.search_indicator.dto import SearchIndicatorRequest
from src.application.search_indicator.pipeline import SearchIndicatorPipeline
from src.core.exceptions import WorldBankMCPError
from src.core.result import ClarificationNeeded, DataResult, NotFound


class ToolHandlers:
    def __init__(
        self,
        search_pipeline: SearchIndicatorPipeline,
        data_pipeline: GetIndicatorDataPipeline,
        country_pipeline: GetCountryIndicatorPipeline,
        export_pipeline: ExportReportPipeline,
    ):
        self._search_pipeline = search_pipeline
        self._data_pipeline = data_pipeline
        self._country_pipeline = country_pipeline
        self._export_pipeline = export_pipeline

    async def handle_search_indicator(self, arguments: dict) -> list[TextContent]:
        try:
            request = SearchIndicatorRequest(topic=arguments["topic"])
            result = await self._search_pipeline.execute(request)
            
            if isinstance(result, NotFound):
                return [TextContent(type="text", text=f"Not Found: {result.reason}")]
                
            # List of IndicatorCandidate
            data = [asdict(c) for c in result]
            return [TextContent(type="text", text=json.dumps(data, indent=2))]
            
        except Exception as e:
            return self._handle_exception(e)

    async def handle_get_indicator_data(self, arguments: dict) -> list[TextContent]:
        try:
            request = GetIndicatorDataRequest(
                indicator_code=arguments["indicator_code"],
                country_code=arguments["country_code"],
                start_year=arguments["start_year"],
                end_year=arguments["end_year"],
                dimensions=arguments.get("dimensions")
            )
            result = await self._data_pipeline.execute(request)
            
            return self._format_data_result(result)
            
        except Exception as e:
            return self._handle_exception(e)

    async def handle_get_country_indicator(self, arguments: dict) -> list[TextContent]:
        try:
            request = GetCountryIndicatorRequest(
                country_name=arguments["country_name"],
                indicator_topic=arguments["indicator_topic"],
                start_year=arguments["start_year"],
                end_year=arguments["end_year"],
                dimensions=arguments.get("dimensions")
            )
            result = await self._country_pipeline.execute(request)
            
            if isinstance(result, ClarificationNeeded):
                return self._format_clarification(result)
            elif isinstance(result, NotFound):
                return [TextContent(type="text", text=f"Not Found: {result.reason}")]
                
            return self._format_data_result(result)
            
        except Exception as e:
            return self._handle_exception(e)

    async def handle_export_report(self, arguments: dict) -> list[TextContent]:
        try:
            request = ExportReportRequest(
                country_name=arguments["country_name"],
                indicator_topics=arguments["indicator_topics"],
                start_year=arguments["start_year"],
                end_year=arguments["end_year"],
                format=arguments["format"],
                destination=arguments["destination"],
                dimensions=arguments.get("dimensions")
            )
            result = await self._export_pipeline.execute(request)
            
            if isinstance(result, ClarificationNeeded):
                return self._format_clarification(result)
            elif isinstance(result, NotFound):
                return [TextContent(type="text", text=f"Export Failed: {result.reason}")]
                
            # result is a string file path
            return [TextContent(type="text", text=f"Success: Report exported to {result}")]
            
        except Exception as e:
            return self._handle_exception(e)

    def _format_data_result(self, result: DataResult) -> list[TextContent]:
        data = asdict(result.series)
        warnings = result.coverage_warnings
        
        response = {
            "series": data,
            "coverage_warnings": warnings
        }
        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    def _format_clarification(self, result: ClarificationNeeded) -> list[TextContent]:
        response = {
            "error": "Clarification Needed",
            "context": result.context,
            "candidates": [asdict(c) for c in result.candidates]
        }
        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    def _handle_exception(self, e: Exception) -> list[TextContent]:
        if isinstance(e, WorldBankMCPError):
            return [TextContent(type="text", text=f"Error ({type(e).__name__}): {str(e)}")]
        return [TextContent(type="text", text=f"Internal Error: {str(e)}")]
