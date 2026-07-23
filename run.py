"""run.py — Entrypoint for the World Bank MCP server."""
import asyncio

import mcp.server.stdio
from mcp.server import Server

from src.application.export_report.pipeline import ExportReportPipeline
from src.application.get_country_indicator.pipeline import GetCountryIndicatorPipeline
from src.application.get_indicator_data.pipeline import GetIndicatorDataPipeline
from src.application.search_indicator.pipeline import SearchIndicatorPipeline
from src.infrastructure.file_export.csv_writer import CSVWriter
from src.infrastructure.file_export.excel_writer import ExcelWriter
from src.infrastructure.file_export.json_writer import JSONWriter
from src.infrastructure.worldbank_client.data_client import DataClient
from src.infrastructure.worldbank_client.search_client import SearchClient
from src.presentation.mcp.server import create_mcp_server
from src.presentation.mcp.tool_handlers import ToolHandlers


async def run() -> None:
    # 1. Instantiate infrastructure
    search_client = SearchClient()
    data_client = DataClient()
    
    writers = {
        "csv": CSVWriter(),
        "xlsx": ExcelWriter(),
        "json": JSONWriter()
    }

    # 2. Instantiate application pipelines
    search_pipeline = SearchIndicatorPipeline(search_port=search_client)
    data_pipeline = GetIndicatorDataPipeline(data_port=data_client)
    country_pipeline = GetCountryIndicatorPipeline(search_port=search_client, data_port=data_client)
    export_pipeline = ExportReportPipeline(search_port=search_client, data_port=data_client, writers=writers)

    # 3. Instantiate tool handlers
    handlers = ToolHandlers(
        search_pipeline=search_pipeline,
        data_pipeline=data_pipeline,
        country_pipeline=country_pipeline,
        export_pipeline=export_pipeline,
    )

    # 4. Create and start the MCP server
    server: Server = create_mcp_server(handlers)
    
    # Run over stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(run())
