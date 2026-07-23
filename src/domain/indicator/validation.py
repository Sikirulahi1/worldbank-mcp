"""validation.py — Validation rules for query parameters."""
import datetime
import re

from src.core.exceptions import IndicatorValidationError


def validate_indicator_code(code: str) -> None:
    if not code or not code.strip():
        raise IndicatorValidationError("Indicator code cannot be empty.")
        
    if not re.match(r"^[A-Z0-9_\.]+$", code):
        raise IndicatorValidationError(f"Invalid indicator code syntax: '{code}'")


def validate_year_range(start_year: int, end_year: int) -> None:
    if start_year > end_year:
        raise IndicatorValidationError(f"Start year ({start_year}) cannot be after end year ({end_year}).")
        
    current_year = datetime.datetime.now().year
    
    if start_year < 1900 or end_year > current_year:
        raise IndicatorValidationError(f"Year range {start_year}-{end_year} is outside plausible bounds (1900-{current_year}).")


def validate_country_code(code: str) -> None:
    if not code or not code.strip():
        raise IndicatorValidationError("Country code cannot be empty.")
        
    if not re.match(r"^[A-Z]{2,3}$", code):
        raise IndicatorValidationError(f"Country code must be a 2 or 3 letter uppercase ISO code: '{code}'")
