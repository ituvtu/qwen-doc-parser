import requests
import json
import time

# URL твого локального сервера
API_URL = "http://127.0.0.1:7860/api/v1/extract"
# Шлях до будь-якої тестової картинки
IMAGE_PATH = "app/assets/reference_image.jpg"

def test_extraction():
    print(f"📡 Sending {IMAGE_PATH} to {API_URL}...")
    
    start_time = time.time()
    
    try:
        # Відкриваємо файл у бінарному режимі
        with open(IMAGE_PATH, "rb") as f:
            files = {"file": ("document.jpg", f, "image/jpeg")}
            
            # Робимо POST запит
            response = requests.post(API_URL, files=files)
            
        duration = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ Success! ({duration:.2f}s)")
            data = response.json()
            
            # Виводимо красиво
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Перевірка чи є дані
            if "elements" in data:
                print(f"\n📊 Extracted {len(data['elements'])} elements.")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except FileNotFoundError:
        print(f"❌ Файл {IMAGE_PATH} не знайдено! Поклади якусь картинку поруч зі скриптом.")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_extraction()