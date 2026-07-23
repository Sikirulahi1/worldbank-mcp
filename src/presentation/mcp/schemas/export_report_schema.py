"""export_report_schema.py — JSON schema for the export_report MCP tool."""
from src.core.constants import SUPPORTED_EXPORT_FORMATS


EXPORT_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "country_name": {
            "type": "string",
            "description": "The plain-language name of the country."
        },
        "indicator_topics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of concepts or topics to include in the report."
        },
        "start_year": {
            "type": "integer",
            "description": "The 4-digit start year of the data range."
        },
        "end_year": {
            "type": "integer",
            "description": "The 4-digit end year of the data range."
        },
        "format": {
            "type": "string",
            "enum": SUPPORTED_EXPORT_FORMATS,
            "description": "The format of the file to export (e.g., 'csv', 'xlsx', 'json')."
        },
        "destination": {
            "type": "string",
            "description": "The absolute path where the report should be saved on the local filesystem."
        },
        "dimensions": {
            "type": "object",
            "description": "Optional advanced dimensions to filter data.",
            "additionalProperties": {"type": "string"}
        }
    },
    "required": ["country_name", "indicator_topics", "start_year", "end_year", "format", "destination"]
}
