import pandas as pd
import os
import io
import pytest
from app.utils.export import parse_json_to_df, save_csv_file, save_excel_file

@pytest.fixture
def sample_json_data():
    return {
        "elements": [
            {"semantic_label": "Invoice Num", "content": "INV-001"},
            {"semantic_label": "Total", "content": "$100.00"}
        ]
    }

def test_dataframe_structure(sample_json_data):
    df = parse_json_to_df(sample_json_data)
    assert list(df.columns) == ["Field", "Value"]
    assert df.iloc[0]["Field"] == "Invoice Num"
    assert df.iloc[0]["Value"] == "INV-001"

def test_save_csv_content(sample_json_data):
    path = save_csv_file(sample_json_data)
    
    try:
        df = pd.read_csv(path)
        assert len(df) == 2
        row = df[df["Field"] == "Total"].iloc[0]
        assert row["Value"] == "$100.00"
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_save_excel_content(sample_json_data):
    path = save_excel_file(sample_json_data)
    
    try:
        df = pd.read_excel(path)
        assert len(df) == 2
        assert "Field" in df.columns
        assert str(df.iloc[0]["Value"]) == "INV-001"
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_export_handles_empty_data():
    empty_data = {"elements": []}
    df = parse_json_to_df(empty_data)
    assert df.empty
    assert list(df.columns) == ["Field", "Value"]