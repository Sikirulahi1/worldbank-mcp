"""field_analysis.py — Classifies observation fields as constant or varying."""
from typing import Any

from src.domain.indicator.entities import Observation


def analyze_fields(observations: list[Observation]) -> tuple[dict[str, Any], set[str]]:
    if not observations:
        return {}, set()

    all_keys = observations[0].raw_fields.keys()
    constant_fields = {}
    varying_fields = set()
    
    for key in all_keys:
        first_val = observations[0].raw_fields[key]
        is_constant = all(obs.raw_fields.get(key) == first_val for obs in observations)
        
        if is_constant:
            constant_fields[key] = first_val
        else:
            varying_fields.add(key)
            
    return constant_fields, varying_fields
