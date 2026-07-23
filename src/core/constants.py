"""Named constants shared across all layers of worldbank-mcp."""

# ---------------------------------------------------------------------------
# World Bank database priority for duplicate-indicator tie-breaking (ADR-002).
# When the same indicator concept appears under multiple database IDs, the
# first match in this list wins. Anything not listed falls back to
# alphabetical order.
# ---------------------------------------------------------------------------
DATABASE_PRIORITY: list[str] = [
    "WB_WDI",
    "WB_WDI_GEP",
    "WB_ESG",
    "WB_GS",
    "WB_CLEAR",
]

# Maximum candidates kept after ranking and deduplication.
MAX_CANDIDATES: int = 10

# @search.score below which a single result is treated as a weak/low-confidence
# match requiring user confirmation instead of auto-resolving (ADR-003).
WEAK_MATCH_SCORE_THRESHOLD: float = 15.0

# Scores below this floor are treated as not-found even if a row exists (ADR-003).
NOT_FOUND_SCORE_FLOOR: float = 10.0

# Ratio required for the top score to auto-resolve over the runner up.
STANDOUT_SCORE_RATIO: float = 1.5

# ---------------------------------------------------------------------------
# World Bank API endpoints
# ---------------------------------------------------------------------------
WORLDBANK_BASE_URL: str = "https://data360api.worldbank.org"
WORLDBANK_SEARCH_PATH: str = "/data360/searchv2"
WORLDBANK_DATA_PATH: str = "/data360/data"
WORLDBANK_METADATA_PATH: str = "/data360/metadata"

# Maximum records per single /data360/data response — paginate with `skip`.
WORLDBANK_PAGE_SIZE: int = 1000

# ---------------------------------------------------------------------------
# File export
# ---------------------------------------------------------------------------
SUPPORTED_EXPORT_FORMATS: list[str] = ["csv", "xlsx", "json"]
