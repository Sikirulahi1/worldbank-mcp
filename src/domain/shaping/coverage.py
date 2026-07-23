"""coverage.py — Identifies gaps and out-of-bounds years in data coverage."""


def analyze_coverage(
    requested_start: int,
    requested_end: int,
    actual_start: int,
    actual_end: int,
    data: dict[str, str | None]
) -> list[str]:
    warnings = []
    
    if requested_start < actual_start:
        warnings.append(f"Requested start {requested_start} is before data begins in {actual_start}.")
        
    if requested_end > actual_end:
        warnings.append(f"Requested end {requested_end} is after data ends in {actual_end}.")
        
    overlap_start = max(requested_start, actual_start)
    overlap_end = min(requested_end, actual_end)
    
    for year in range(overlap_start, overlap_end + 1):
        year_str = str(year)
        if year_str not in data or data[year_str] is None:
            warnings.append(f"Missing data for year {year}.")
            
    return warnings
