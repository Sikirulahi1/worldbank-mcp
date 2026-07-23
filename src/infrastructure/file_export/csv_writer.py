"""csv_writer.py — CSV file writer implementation."""
import csv
import os
from dataclasses import asdict

from typing import Any
import aiofiles

from src.application.ports.file_port import IFileWriter
from src.core.exceptions import ExportError


class CSVWriter(IFileWriter):
    async def write(self, rows: list[dict[str, Any]], destination: str) -> str:
        dest_dir = os.path.dirname(os.path.abspath(destination))
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
            
        try:
            async with aiofiles.open(destination, mode='w', encoding='utf-8', newline='') as f:
                if not rows:
                    return os.path.abspath(destination)
                    
                fieldnames = list(rows[0].keys())
                
                import io
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
                    
                await f.write(output.getvalue())
        except OSError as e:
            raise ExportError(f"Failed to write CSV file to {destination}: {e}") from e
            
        return os.path.abspath(destination)
