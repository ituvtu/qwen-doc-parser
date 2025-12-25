import pytest
from PIL import Image
import io
from app.utils.processing import extract_json_from_text, resize_and_pad_image, convert_padded_bbox_to_gradio

# --- 1. Тести парсера ---

@pytest.mark.parametrize("input_text, expected_key", [
    ('{"key": "val"}', "key"),
    ('Here is JSON: ```json {"key": "val"} ```', "key"),
    ('{"key": "val", "broken": [', "key"),
    ('Some text {"key": "val"} trailing text', "key"),
])
def test_extract_json_variations(input_text, expected_key):
    result = extract_json_from_text(input_text)
    assert expected_key in result, f"Failed to parse: {input_text}"

def test_extract_json_total_failure():
    """Перевірка на повну нісенітницю."""
    result = extract_json_from_text("Not a json at all")
    assert "error" in result
    # FIX: Тепер це пройде, бо ми додали elements у processing.py
    assert result["elements"] == []

# --- 2. Тести зображень ---

def test_resize_and_pad_logic():

    img = Image.new('RGB', (100, 50), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    valid_rect_bytes = buf.getvalue()

    # Target 200x200.
    # Scale calculation: 
    #   W: 200 / 100 = 2.0
    #   H: 200 / 50 = 4.0
    #   Min Scale = 2.0
    # New Size: W=200, H=100 (50*2)
    # Padding X: (200 - 200) / 2 = 0
    # Padding Y: (200 - 100) / 2 = 50
    processed_bytes, padding, orig_size = resize_and_pad_image(valid_rect_bytes, target_size=200)
    
    img_res = Image.open(io.BytesIO(processed_bytes))
    assert img_res.size == (200, 200)
    
    # Перевіряємо кольори
    # (0, 0) - це верхнє поле (padding), має бути білим
    assert img_res.getpixel((0, 0)) == (255, 255, 255)
    
    # (100, 100) - це центр, там має бути червона картинка
    # Оскільки padding_y=50, а висота картинки 100, то картинка займає Y від 50 до 150.
    # Центр (100, 100) точно червоний.
    # (Увага: через JPEG стиснення колір може бути не ідеально (255,0,0), даємо допуск)
    pixel = img_res.getpixel((100, 100))
    assert pixel[0] > 200 # Red component high
    assert pixel[1] < 50  # Green low
    assert pixel[2] < 50  # Blue low
    
    # Перевіряємо розрахунок padding
    # (paste_x, paste_y, new_w, new_h)
    assert padding == (0, 50, 200, 100)

# --- 3. Тести координат ---

def test_bbox_conversion_logic():
    # Канвас 1000x1000.
    # Картинка вклеєна по центру 500x500 (padding 250 з усіх боків).
    padding_info = (250, 250, 500, 500)
    orig_size = (100, 100)
    canvas_size = 1000
    
    # Якщо модель каже "весь канвас" (0,0 -> 1000,1000) - це вихід за межі реального контенту.
    # Але якщо модель каже "центр канвасу" (де і є картинка):
    # (250, 250) на канвасі -> це (0, 0) на картинці.
    
    bbox_center = [250, 250, 750, 750] 
    
    res = convert_padded_bbox_to_gradio(bbox_center, padding_info, orig_size, canvas_size)
    
    # Має перетворитися на повну оригінальну картинку [0, 0, 100, 100]
    # Допускаємо похибку +/- 1 піксель через float перетворення
    assert -1 <= res[0] <= 1
    assert -1 <= res[1] <= 1
    assert 99 <= res[2] <= 101
    assert 99 <= res[3] <= 101
