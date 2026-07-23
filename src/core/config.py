"""
worldbank-mcp settings loaded from environment / .env file.

Env var naming convention:
  - .env file:  SCREAMING_SNAKE_CASE  (e.g. WORLDBANK_BASE_URL)
  - Python:     snake_case attributes  (e.g. worldbank_base_url)
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Required environment variable {key} is not set")
    return value


class Settings:
    worldbank_base_url: str
    worldbank_timeout_seconds: int
    worldbank_max_retries: int
    export_output_dir: str
    log_level: str

    def __init__(self) -> None:
        self.worldbank_base_url = os.getenv(
            "WORLDBANK_BASE_URL", "https://data360api.worldbank.org"
        )
        self.worldbank_timeout_seconds = int(
            os.getenv("WORLDBANK_TIMEOUT_SECONDS", "30")
        )
        self.worldbank_max_retries = int(
            os.getenv("WORLDBANK_MAX_RETRIES", "3")
        )
        self.export_output_dir = os.getenv("EXPORT_OUTPUT_DIR", "./exports")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
