"""resolution.py — Resolves plain-language country names to Country entities."""
import re

from src.core.result import ClarificationNeeded, NotFound
from src.domain.country.entities import Country
from src.domain.country.reference_data import COUNTRIES


def _normalize(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def resolve_country(name: str) -> Country | ClarificationNeeded | NotFound:
    normalized_input = _normalize(name)
    if not normalized_input:
        return NotFound(reason="Empty or invalid country name provided")

    exact_matches: list[Country] = []
    partial_matches: list[Country] = []

    for country in COUNTRIES:
        if normalized_input in (_normalize(country.iso2), _normalize(country.iso3), _normalize(country.name)):
            exact_matches.append(country)
            continue
            
        matched_alias = False
        for alias in country.aliases:
            if normalized_input == _normalize(alias):
                exact_matches.append(country)
                matched_alias = True
                break
                
        if matched_alias:
            continue
            
        if normalized_input in _normalize(country.name):
            partial_matches.append(country)
            continue
            
        for alias in country.aliases:
            if normalized_input in _normalize(alias):
                partial_matches.append(country)
                break

    if len(exact_matches) == 1:
        return exact_matches[0]
        
    candidates = exact_matches if exact_matches else partial_matches
    
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        return ClarificationNeeded(
            candidates=candidates,
            context=f"'{name}' matched multiple distinct countries."
        )
        
    return NotFound(reason=f"No country matched '{name}'.")
