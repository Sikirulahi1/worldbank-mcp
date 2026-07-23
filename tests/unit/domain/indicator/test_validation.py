"""Unit tests for domain/indicator/validation.py."""
import pytest

from src.core.exceptions import IndicatorValidationError
from src.domain.indicator.validation import (
    validate_country_code,
    validate_indicator_code,
    validate_year_range,
)


def test_validate_indicator_code():
    # Valid
    validate_indicator_code("SP.POP.TOTL")
    validate_indicator_code("WB_ESG_NY_GDP_MKTP_KD_ZG")
    
    # Invalid
    with pytest.raises(IndicatorValidationError):
        validate_indicator_code("")
        
    with pytest.raises(IndicatorValidationError):
        validate_indicator_code("drop table;")
        
    with pytest.raises(IndicatorValidationError):
        validate_indicator_code("sp.pop.totl")  # lowercase not standard


def test_validate_year_range():
    # Valid
    validate_year_range(2000, 2020)
    validate_year_range(2020, 2020)
    
    # Invalid: inverted
    with pytest.raises(IndicatorValidationError, match="cannot be after"):
        validate_year_range(2020, 2010)
        
    # Invalid: bounds
    with pytest.raises(IndicatorValidationError, match="plausible bounds"):
        validate_year_range(1800, 2000)
        
    import datetime
    current_year = datetime.datetime.now().year
    with pytest.raises(IndicatorValidationError, match="plausible bounds"):
        validate_year_range(2000, current_year + 1)


def test_validate_country_code():
    # Valid
    validate_country_code("US")
    validate_country_code("NGA")
    
    # Invalid
    with pytest.raises(IndicatorValidationError):
        validate_country_code("Nigeria")  # Not an ISO code
        
    with pytest.raises(IndicatorValidationError):
        validate_country_code("ng")  # Must be uppercase
        
    with pytest.raises(IndicatorValidationError):
        validate_country_code("")
