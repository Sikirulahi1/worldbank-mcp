"""file_port.py — Abstract interface for file export operations."""
from typing import Any, Protocol


class IFileWriter(Protocol):
    """Interface for writing indicator data to a file."""
    
    async def write(self, rows: list[dict[str, Any]], destination: str) -> str:
        """Write tabular rows to the destination."""
        ...
