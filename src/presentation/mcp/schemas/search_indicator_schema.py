"""search_indicator_schema.py — JSON schema for the search_indicator MCP tool."""

SEARCH_INDICATOR_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {
            "type": "string",
            "description": "The concept or topic to search for (e.g., 'GDP', 'population', 'poverty')."
        }
    },
    "required": ["topic"]
}
