"""Unit tests for domain/indicator/disambiguation.py."""
import json
from pathlib import Path
import pytest

from src.core.result import ClarificationNeeded, NotFound
from src.domain.indicator.disambiguation import disambiguate_candidates
from src.domain.indicator.entities import IndicatorCandidate


def test_outcome_c_not_found():
    # Empty list
    result = disambiguate_candidates([])
    assert isinstance(result, NotFound)
    
    # List with items below the floor
    candidates = [
        IndicatorCandidate("ID1", "A", "DB", 9.9),
        IndicatorCandidate("ID2", "B", "DB", 5.0)
    ]
    result2 = disambiguate_candidates(candidates)
    assert isinstance(result2, NotFound)


def test_outcome_a_auto_resolve():
    # Single strong match
    candidates = [IndicatorCandidate("ID1", "GDP", "WB_ESG", 21.5)]
    result = disambiguate_candidates(candidates)
    assert isinstance(result, IndicatorCandidate)
    assert result.idno == "ID1"
    
    # Multiple candidates but all identical concept (graceful fallback)
    cands_same = [
        IndicatorCandidate("ID1", "GDP", "WB_ESG", 21.5),
        IndicatorCandidate("ID2", "gdp", "WB_GS", 20.0)
    ]
    result2 = disambiguate_candidates(cands_same)
    assert isinstance(result2, IndicatorCandidate)
    assert result2.idno == "ID1"


def test_outcome_b_ask_user_weak_match():
    # Single weak match (score between 10.0 and 15.0)
    candidates = [IndicatorCandidate("ID1", "GDP", "WB_ESG", 14.9)]
    result = disambiguate_candidates(candidates)
    
    assert isinstance(result, ClarificationNeeded)
    assert len(result.candidates) == 1
    assert result.candidates[0].idno == "ID1"
    assert "low" in result.context.lower()


def test_outcome_b_ask_user_multiple_concepts():
    # Multiple distinct concepts
    candidates = [
        IndicatorCandidate("ID1", "GDP growth", "DB", 21.5),
        IndicatorCandidate("ID2", "GDP per capita", "DB", 20.5)
    ]
    result = disambiguate_candidates(candidates)
    
    assert isinstance(result, ClarificationNeeded)
    assert len(result.candidates) == 2
    assert result.candidates[0].idno == "ID1"
    assert "multiple" in result.context.lower()


def test_outcome_a_clear_standout():
    # Top score is > 1.5x the runner up (117 vs 75)
    candidates = [
        IndicatorCandidate("ID1", "Clear Winner", "DB", 117.0),
        IndicatorCandidate("ID2", "Loser", "DB", 75.0)
    ]
    result = disambiguate_candidates(candidates)
    
    assert isinstance(result, IndicatorCandidate)
    assert result.idno == "ID1"


def test_with_real_poverty_fixture():
    fixture_path = Path("tests/fixtures/sample_responses/search_poverty_ambiguous.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    candidates = [
        IndicatorCandidate(
            idno=item["series_description"]["idno"],
            name=item["series_description"]["name"],
            database_id=item["series_description"]["database_id"],
            search_score=item.get("@search.score", 0.0)
        )
        for item in data.get("value", [])
    ]
    
    result = disambiguate_candidates(candidates)
    assert isinstance(result, ClarificationNeeded)
    assert len(result.candidates) > 1
