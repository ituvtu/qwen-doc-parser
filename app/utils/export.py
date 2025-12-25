import pandas as pd
import json
import tempfile
import os

def parse_json_to_df(json_data: dict) -> pd.DataFrame:
    """Перетворює JSON моделі у DataFrame (таблицю)."""
    data = []
    if "elements" in json_data and isinstance(json_data["elements"], list):
        for item in json_data["elements"]:
            label = item.get("semantic_label") or item.get("label") or "unknown"
            content = item.get("content") or item.get("text_content") or ""
            
            data.append({"Field": label, "Value": content})
    
    if not data:
        return pd.DataFrame(columns=["Field", "Value"])
        
    return pd.DataFrame(data)

def save_json_file(json_data: dict) -> str:
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
        return f.name

def save_csv_file(json_data: dict) -> str:
    df = parse_json_to_df(json_data)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
        df.to_csv(f, index=False)
        return f.name

def save_excel_file(json_data: dict) -> str:
    df = parse_json_to_df(json_data)
    fd, path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    df.to_excel(path, index=False)
    return path