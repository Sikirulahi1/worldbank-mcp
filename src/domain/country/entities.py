"""entities.py — Country domain entity."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Country:
    iso2:    str
    iso3:    str
    name:    str
    aliases: list[str] = field(default_factory=list)
