"""Unit tests for domain/country/resolution.py."""
import pytest

from src.core.result import ClarificationNeeded, NotFound
from src.domain.country.entities import Country
from src.domain.country.resolution import resolve_country


def test_resolve_clean_match():
    # Exact match on ISO-2
    result = resolve_country("NG")
    assert isinstance(result, Country)
    assert result.iso3 == "NGA"
    
    # Exact match on name
    result = resolve_country("Nigeria")
    assert isinstance(result, Country)
    assert result.iso3 == "NGA"
    
    # Exact match on alias
    result = resolve_country("Ivory Coast")
    assert isinstance(result, Country)
    assert result.iso3 == "CIV"


def test_resolve_ambiguous_match():
    # "Congo" should match both Republic of Congo and DRC
    result = resolve_country("Congo")
    assert isinstance(result, ClarificationNeeded)
    assert len(result.candidates) == 2
    assert any(c.iso3 == "COG" for c in result.candidates)
    assert any(c.iso3 == "COD" for c in result.candidates)
    
    # "Korea" should match both North and South
    result = resolve_country("Korea")
    assert isinstance(result, ClarificationNeeded)
    assert len(result.candidates) == 2


def test_resolve_misspelled_or_partial_match():
    # Partial match: "United States of America" (actually an exact alias, but what about "United State"?)
    result = resolve_country("United State")
    assert isinstance(result, Country)
    assert result.iso3 == "USA"
    
    # Punctuation/case differences
    result = resolve_country("cote divoire")
    assert isinstance(result, Country)
    assert result.iso3 == "CIV"


def test_resolve_no_match():
    # Complete nonsense
    result = resolve_country("xyzzy")
    assert isinstance(result, NotFound)
    assert "No country matched" in result.reason
    
    # Empty string
    result = resolve_country("")
    assert isinstance(result, NotFound)
