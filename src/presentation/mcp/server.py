"""server.py — Registers all four MCP tools and returns the server instance."""
from mcp.server import Server
from mcp.types import Tool

from src.presentation.mcp.schemas.export_report_schema import EXPORT_REPORT_SCHEMA
from src.presentation.mcp.schemas.get_country_indicator_schema import GET_COUNTRY_INDICATOR_SCHEMA
from src.presentation.mcp.schemas.get_indicator_data_schema import GET_INDICATOR_DATA_SCHEMA
from src.presentation.mcp.schemas.search_indicator_schema import SEARCH_INDICATOR_SCHEMA
from src.presentation.mcp.tool_handlers import ToolHandlers


def create_mcp_server(handlers: ToolHandlers) -> Server:
    server = Server("worldbank-mcp")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return [
            Tool(
                name="search_indicator",
                description="Search for World Bank indicators by topic. Returns a ranked, deduplicated list of candidates.",
                inputSchema=SEARCH_INDICATOR_SCHEMA,
            ),
            Tool(
                name="get_indicator_data",
                description="Fetch data for a specific indicator and country over a year range. Assumes you already know the exact indicator code.",
                inputSchema=GET_INDICATOR_DATA_SCHEMA,
            ),
            Tool(
                name="get_country_indicator",
                description="The primary tool to get data: resolves a country name, searches for an indicator topic, and fetches the data. Handles disambiguation and prompts for clarification if needed.",
                inputSchema=GET_COUNTRY_INDICATOR_SCHEMA,
            ),
            Tool(
                name="export_report",
                description="Export a wide-table report containing multiple indicators for a country over a year range. Saves locally to csv, xlsx, or json.",
                inputSchema=EXPORT_REPORT_SCHEMA,
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list:
        if name == "search_indicator":
            return await handlers.handle_search_indicator(arguments)
        elif name == "get_indicator_data":
            return await handlers.handle_get_indicator_data(arguments)
        elif name == "get_country_indicator":
            return await handlers.handle_get_country_indicator(arguments)
        elif name == "export_report":
            return await handlers.handle_export_report(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    return server
