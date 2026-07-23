"""test_file_writers.py — Tests for JSON and CSV file writers."""
import json
import os
from pathlib import Path

import pytest

from src.core.exceptions import ExportError
from src.infrastructure.file_export.csv_writer import CSVWriter
from src.infrastructure.file_export.json_writer import JSONWriter


@pytest.fixture
def sample_rows():
    return [
        {"year": "2020", "GDP": "21.06"},
        {"year": "2021", "GDP": "23.32"},
    ]


@pytest.mark.asyncio
async def test_json_writer(tmp_path: Path, sample_rows):
    dest = tmp_path / "test_output.json"
    writer = JSONWriter()
    
    path = await writer.write(sample_rows, str(dest))
    assert os.path.exists(path)
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert len(data) == 2
    assert data[0]["year"] == "2020"
    assert data[0]["GDP"] == "21.06"


@pytest.mark.asyncio
async def test_csv_writer(tmp_path: Path, sample_rows):
    dest = tmp_path / "test_output.csv"
    writer = CSVWriter()
    
    path = await writer.write(sample_rows, str(dest))
    assert os.path.exists(path)
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Header + 2 rows
    assert len(lines) == 3
    assert "year,GDP" in lines[0]
    assert "2020,21.06" in lines[1]


@pytest.mark.asyncio
async def test_json_writer_directory_creation(tmp_path: Path, sample_rows):
    # Test writing to a nested directory that doesn't exist yet
    dest = tmp_path / "nested" / "folder" / "test_output.json"
    writer = JSONWriter()
    
    path = await writer.write(sample_rows, str(dest))
    assert os.path.exists(path)
