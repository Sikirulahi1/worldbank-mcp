"""excel_writer.py — XLSX file writer implementation using pandas."""
import os
from typing import Any

import pandas as pd

from src.application.ports.file_port import IFileWriter
from src.core.exceptions import ExportError


class ExcelWriter(IFileWriter):
    async def write(self, rows: list[dict[str, Any]], destination: str) -> str:
        dest_dir = os.path.dirname(os.path.abspath(destination))
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
            
        try:
            if not rows:
                # Produce empty file if no observations
                df = pd.DataFrame()
                df.to_excel(destination, index=False, engine='openpyxl')
                return os.path.abspath(destination)
                
            df = pd.DataFrame(rows)
            # pandas to_excel is synchronous, but we can call it directly for this CLI tool
            df.to_excel(destination, index=False, engine='openpyxl')
        except Exception as e:
            raise ExportError(f"Failed to write Excel file to {destination}: {e}") from e
            
        return os.path.abspath(destination)
