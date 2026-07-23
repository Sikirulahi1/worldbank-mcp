"""test_response_parser.py — Tests for the raw JSON parser."""
import json
from pathlib import Path

import pytest

from src.core.exceptions import WorldBankResponseError
from src.infrastructure.worldbank_client.response_parser import (
    parse_observations,
    parse_search_candidates,
)


def load_fixture(name: str) -> dict:
    path = Path("tests/fixtures/sample_responses") / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_parse_search_candidates_clean():
    payload = load_fixture("search_gdp_clean.json")
    candidates = parse_search_candidates(payload)
    
    assert len(candidates) > 0
    assert candidates[0].idno == "WB_HNP_SP_POP_TOTL_ZS"
    assert candidates[0].search_score > 0.0


def test_parse_search_candidates_empty():
    payload = load_fixture("search_nonsense_empty.json")
    candidates = parse_search_candidates(payload)
    
    assert len(candidates) == 0


def test_parse_search_malformed():
    with pytest.raises(WorldBankResponseError, match="must be a JSON object"):
        parse_search_candidates([])
        
    with pytest.raises(WorldBankResponseError, match="missing a valid 'value' array"):
        parse_search_candidates({})
        
    with pytest.raises(WorldBankResponseError, match="Missing 'series_description'"):
        parse_search_candidates({"value": [{"@search.score": 10.0}]})


def test_parse_observations_clean():
    payload = load_fixture("data_nigeria_gdp_1999_2010.json")
    obs = parse_observations(payload, "WB_ESG_NY_GDP_MKTP_KD_ZG", "NGA")
    
    assert len(obs) > 0
    assert obs[0].indicator == "WB_ESG_NY_GDP_MKTP_KD_ZG"
    assert obs[0].ref_area == "NGA"
    assert obs[0].time_period is not None
    assert obs[0].obs_value is not None


def test_parse_observations_empty():
    payload = load_fixture("data_zero_records.json")
    obs = parse_observations(payload, "IND1", "USA")
    assert len(obs) == 0


def test_parse_observations_malformed():
    with pytest.raises(WorldBankResponseError):
        parse_observations([], "IND1", "USA")
        
    with pytest.raises(WorldBankResponseError, match="missing 'TIME_PERIOD'"):
        parse_observations({"value": [{"OBS_VALUE": 10}]}, "IND1", "USA")
