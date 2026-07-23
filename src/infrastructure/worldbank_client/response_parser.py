"""response_parser.py — Translates raw JSON into domain entities."""
from typing import Any

from src.core.exceptions import WorldBankResponseError
from src.domain.indicator.entities import IndicatorCandidate, Observation


def parse_search_candidates(payload: dict[str, Any]) -> list[IndicatorCandidate]:
    if not isinstance(payload, dict):
        raise WorldBankResponseError("Search response payload must be a JSON object.")
        
    values = payload.get("value")
    if not isinstance(values, list):
        raise WorldBankResponseError("Search response is missing a valid 'value' array.")
        
    candidates = []
    for item in values:
        try:
            score = float(item.get("@search.score", 0.0))
            series_desc = item.get("series_description")
            if not isinstance(series_desc, dict):
                raise WorldBankResponseError("Missing 'series_description' in search result.")
                
            idno = series_desc["idno"]
            name = series_desc["name"]
            database_id = series_desc["database_id"]
            
            candidates.append(IndicatorCandidate(
                idno=str(idno),
                name=str(name),
                database_id=str(database_id),
                search_score=score
            ))
        except KeyError as e:
            raise WorldBankResponseError(f"Search result missing required field: {e}")
        except (ValueError, TypeError) as e:
            raise WorldBankResponseError(f"Malformed search result field: {e}")
            
    return candidates


def parse_observations(payload: dict[str, Any], indicator_code: str, country_code: str) -> list[Observation]:
    if not isinstance(payload, dict):
        raise WorldBankResponseError("Data response payload must be a JSON object.")
        
    values = payload.get("value")
    if not isinstance(values, list):
        raise WorldBankResponseError("Data response is missing a valid 'value' array.")
        
    observations = []
    for item in values:
        time_period = item.get("TIME_PERIOD")
        if not time_period:
            raise WorldBankResponseError("Observation row missing 'TIME_PERIOD'.")
            
        try:
            obs_value_raw = item.get("OBS_VALUE")
            obs_value = str(obs_value_raw) if obs_value_raw is not None else None
            
            raw_fields = {k: v for k, v in item.items() if k not in ("TIME_PERIOD", "OBS_VALUE", "INDICATOR", "REF_AREA")}
            
            observations.append(Observation(
                indicator=item.get("INDICATOR", indicator_code),
                ref_area=item.get("REF_AREA", country_code),
                time_period=str(time_period),
                obs_value=obs_value,
                raw_fields=raw_fields
            ))
        except Exception as e:
            raise WorldBankResponseError(f"Malformed observation row: {e}")
            
    return observations
