"""metadata_port.py — Abstract interface for metadata fetching."""
from typing import Protocol


class IMetadataPort(Protocol):
    """Interface for fetching indicator metadata."""
    
    async def get_coverage(self, indicator_code: str) -> tuple[int, int]:
        """
        Fetch the actual available year range for an indicator.
        
        Returns:
            Tuple of (start_year, end_year)
        """
        ...
