"""get_indicator_data_schema.py — JSON schema for the get_indicator_data MCP tool."""

GET_INDICATOR_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "indicator_code": {
            "type": "string",
            "description": "The exact World Bank indicator code (e.g., 'NY.GDP.MKTP.CD')."
        },
        "country_code": {
            "type": "string",
            "description": "The exact 3-letter ISO country code (e.g., 'USA', 'NGA')."
        },
        "start_year": {
            "type": "integer",
            "description": "The 4-digit start year of the data range (e.g., 2010)."
        },
        "end_year": {
            "type": "integer",
            "description": "The 4-digit end year of the data range (e.g., 2020)."
        },
        "dimensions": {
            "type": "object",
            "description": "Optional advanced dimensions to filter data (e.g., by age or gender).",
            "additionalProperties": {"type": "string"}
        }
    },
    "required": ["indicator_code", "country_code", "start_year", "end_year"]
}
