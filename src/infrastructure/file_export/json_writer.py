"""json_writer.py — JSON file writer implementation."""
import json
import os
from dataclasses import asdict

from typing import Any
import aiofiles

from src.application.ports.file_port import IFileWriter
from src.core.exceptions import ExportError


class JSONWriter(IFileWriter):
    async def write(self, rows: list[dict[str, Any]], destination: str) -> str:
        dest_dir = os.path.dirname(os.path.abspath(destination))
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
            
        try:
            async with aiofiles.open(destination, mode='w', encoding='utf-8') as f:
                content = json.dumps(rows, indent=2)
                await f.write(content)
        except OSError as e:
            raise ExportError(f"Failed to write JSON file to {destination}: {e}") from e
            
        return os.path.abspath(destination)
