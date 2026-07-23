"""table_merge.py — Merges multiple indicator series into a single wide table."""
from src.domain.indicator.entities import IndicatorSeries


def merge_series(series_list: list[IndicatorSeries]) -> list[dict[str, str | None]]:
    if not series_list:
        return []
        
    all_years = set()
    for series in series_list:
        all_years.update(series.data.keys())
        
    sorted_years = sorted(list(all_years))
    
    rows = []
    for year in sorted_years:
        row = {"year": year}
        for series in series_list:
            row[series.indicator] = series.data.get(year)
        rows.append(row)
        
    return rows
