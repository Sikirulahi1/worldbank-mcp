"""Unit tests for domain/indicator/deduplication.py."""
import json
from pathlib import Path

from src.domain.indicator.deduplication import deduplicate_candidates
from src.domain.indicator.entities import IndicatorCandidate


def test_deduplicate_with_real_fixture():
    fixture_path = Path("tests/fixtures/sample_responses/search_gdp_duplicates.json")
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
    
    deduped = deduplicate_candidates(candidates)
    
    # In the fixture, "GDP growth (annual %)" appears 3 times (WB_ESG, WB_GS, WB_CLEAR)
    # Deduplication should collapse these to 1.
    gdp_growth_cands = [c for c in deduped if c.name == "GDP growth (annual %)"]
    assert len(gdp_growth_cands) == 1
    
    # WB_ESG is higher priority than WB_GS and WB_CLEAR, so it should win
    assert gdp_growth_cands[0].database_id == "WB_ESG"
    
    # The other distinct concepts should remain untouched
    distinct_names = {c.name for c in deduped}
    assert "GDP per person employed (constant 2021 PPP $)" in distinct_names
    assert "Government expenditure on education, total (% of GDP)" in distinct_names


def test_deduplicate_fallback_priority():
    candidates = [
        IndicatorCandidate("ID1", "Same Name", "UNKNOWN_DB_B", 10.0),
        IndicatorCandidate("ID2", "Same Name", "UNKNOWN_DB_A", 10.0),
        IndicatorCandidate("ID3", "Same Name", "WB_GS", 10.0),  # In priority list
    ]
    
    deduped = deduplicate_candidates(candidates)
    assert len(deduped) == 1
    # WB_GS should win because it's in the explicit priority list
    assert deduped[0].database_id == "WB_GS"
    
    # If none are in the list, fallback to alphabetical on database_id
    cands_unknown = [
        IndicatorCandidate("ID1", "Same Name", "Z_DB", 10.0),
        IndicatorCandidate("ID2", "Same Name", "A_DB", 10.0),
    ]
    deduped_unk = deduplicate_candidates(cands_unknown)
    assert deduped_unk[0].database_id == "A_DB"


def test_deduplicate_single_item():
    candidates = [IndicatorCandidate("ID1", "Name", "WB_WDI", 10.0)]
    deduped = deduplicate_candidates(candidates)
    assert len(deduped) == 1
    assert deduped[0] == candidates[0]


def test_deduplicate_all_distinct():
    candidates = [
        IndicatorCandidate("ID1", "Concept A", "WB_WDI", 10.0),
        IndicatorCandidate("ID2", "Concept B", "WB_WDI", 10.0),
        IndicatorCandidate("ID3", "Concept C", "WB_ESG", 10.0),
    ]
    deduped = deduplicate_candidates(candidates)
    assert len(deduped) == 3
