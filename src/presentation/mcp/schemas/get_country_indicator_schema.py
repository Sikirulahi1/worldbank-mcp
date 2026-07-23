"""get_country_indicator_schema.py — JSON schema for the get_country_indicator MCP tool."""

GET_COUNTRY_INDICATOR_SCHEMA = {
    "type": "object",
    "properties": {
        "country_name": {
            "type": "string",
            "description": "The plain-language name of the country (e.g., 'Nigeria', 'United States')."
        },
        "indicator_topic": {
            "type": "string",
            "description": "The concept or topic to search for (e.g., 'GDP', 'population')."
        },
        "start_year": {
            "type": "integer",
            "description": "The 4-digit start year of the data range."
        },
        "end_year": {
            "type": "integer",
            "description": "The 4-digit end year of the data range."
        },
        "dimensions": {
            "type": "object",
            "description": "Optional advanced dimensions to filter data.",
            "additionalProperties": {"type": "string"}
        }
    },
    "required": ["country_name", "indicator_topic", "start_year", "end_year"]
}
