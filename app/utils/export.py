import pandas as pd
import json
import tempfile
import os

def parse_json_to_df(json_data: dict) -> pd.DataFrame:
    """Перетворює JSON моделі у DataFrame (таблицю)."""
    data = []
    if "elements" in json_data and isinstance(json_data["elements"], list):
        for item in json_data["elements"]:
            # Беремо тільки потрібні поля
            label = item.get("semantic_label", "unknown")
            content = item.get("content", "")
            data.append({"Field": label, "Value": content})
    
    if not data:
        return pd.DataFrame(columns=["Field", "Value"])
        
    return pd.DataFrame(data)

def save_json_file(json_data: dict) -> str:
    """Зберігає JSON у тимчасовий файл і повертає шлях."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
        return f.name

def save_csv_file(json_data: dict) -> str:
    """Конвертує в CSV і повертає шлях."""
    df = parse_json_to_df(json_data)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
        # index=False прибирає нумерацію рядків (0,1,2...)
        df.to_csv(f, index=False)
        return f.name

def save_excel_file(json_data: dict) -> str:
    """Конвертує в Excel (.xlsx) і повертає шлях."""
    df = parse_json_to_df(json_data)
    
    # Створюємо тимчасовий файл. 
    # Pandas потребує шляху для збереження Excel.
    fd, path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd) # Закриваємо дескриптор, pandas сам відкриє файл
    
    df.to_excel(path, index=False)
    return path