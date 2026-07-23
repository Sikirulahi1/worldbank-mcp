"""test_tool_calls_via_mcp.py — End-to-end tests for MCP tools hitting live World Bank API."""
import json
import os
import sys
import contextlib

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Mark all tests in this file as slow/integration
pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]

# The path to the run.py script
RUN_PY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "run.py"))


@contextlib.asynccontextmanager
async def create_mcp_session():
    """Context manager to spin up the MCP server subprocess and yield a ClientSession."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[RUN_PY_PATH],
        env=os.environ.copy()
    )
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


async def test_search_indicator_tool():
    async with create_mcp_session() as mcp_session:
        """Test search_indicator tool with a known topic."""
        result = await mcp_session.call_tool("search_indicator", {"topic": "GDP"})
        
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        
        data = json.loads(result.content[0].text)
        assert isinstance(data, list)
        assert len(data) > 0
        
        # We should find 'WB_ESG_NY_GDP_MKTP_KD_ZG' somewhere in the GDP results
        assert any("NY_GDP_MKTP_KD_ZG" in c.get("idno", "") for c in data)


async def test_get_indicator_data_tool():
    async with create_mcp_session() as mcp_session:
        """Test get_indicator_data tool with known GDP codes."""
        result = await mcp_session.call_tool(
            "get_indicator_data",
            {
                "indicator_code": "WB_ESG_NY_GDP_MKTP_KD_ZG",
                "country_code": "NGA",
                "start_year": 2010,
                "end_year": 2012
            }
        )
        
        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        
        assert "series" in data
        assert data["series"]["indicator"] == "WB_ESG_NY_GDP_MKTP_KD_ZG"
        assert data["series"]["country"] == "NGA"
        
        # Check that data for 2010, 2011, 2012 is present
        series_data = data["series"]["data"]
        assert "2010" in series_data
        assert "2011" in series_data
        assert "2012" in series_data
        assert isinstance(series_data["2010"], str)


async def test_get_country_indicator_tool_success():
    async with create_mcp_session() as mcp_session:
        """Test get_country_indicator tool with an unambiguous country and topic."""
        result = await mcp_session.call_tool(
            "get_country_indicator",
            {
                "country_name": "Nigeria",
                "indicator_topic": "WB_ESG_NY_GDP_MKTP_KD_ZG",
                "start_year": 2015,
                "end_year": 2015
            }
        )
        
        data = json.loads(result.content[0].text)
        assert "series" in data
        assert data["series"]["country"] == "NGA"
        assert "2015" in data["series"]["data"]


async def test_get_country_indicator_tool_ambiguous():
    async with create_mcp_session() as mcp_session:
        """Test get_country_indicator tool with an ambiguous country name."""
        result = await mcp_session.call_tool(
            "get_country_indicator",
            {
                "country_name": "Congo",
                "indicator_topic": "GDP",
                "start_year": 2015,
                "end_year": 2015
            }
        )
        
        data = json.loads(result.content[0].text)
        # Should ask for clarification
        assert "error" in data
        assert data["error"] == "Clarification Needed"
        assert "context" in data
        assert "candidates" in data
        assert len(data["candidates"]) > 1  # DRC and Republic of Congo


async def test_export_report_tool(tmp_path):
    async with create_mcp_session() as mcp_session:
        """Test export_report tool creating a CSV file."""
        dest_path = tmp_path / "test_report.csv"
        
        result = await mcp_session.call_tool(
            "export_report",
            {
                "country_name": "Nigeria",
                "indicator_topics": ["WB_ESG_NY_GDP_MKTP_KD_ZG"],
                "start_year": 2019,
                "end_year": 2020,
                "format": "csv",
                "destination": str(dest_path)
            }
        )
        
        text = result.content[0].text
        assert "Success" in text
        assert str(dest_path) in text
        
        # Ensure file was actually created and has content
        assert dest_path.exists()
        assert dest_path.stat().st_size > 0
        
        content = dest_path.read_text()
        assert "year" in content.lower()
        assert "GDP" in content
