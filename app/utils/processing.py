import io
import base64
import re
import json
from typing import Tuple, Dict, Any, List

from PIL import Image, ImageDraw, ImageFont

def resize_and_pad_image(image_bytes: bytes, target_size: int = 1280) -> Tuple[bytes, Tuple[int, int, int, int], Tuple[int, int]]:
    """
    Вписує зображення в квадрат target_size x target_size, додаючи білі поля.
    Повертає:
      - байти нового зображення
      - padding_info (x_offset, y_offset, new_width, new_height) - треба для перерахунку координат
      - original_size (w, h)
    """
    with Image.open(io.BytesIO(image_bytes)) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        orig_w, orig_h = img.size
        
        # 1. Розрахунок масштабу (зберігаємо пропорції)
        scale = min(target_size / orig_w, target_size / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        
        # 2. Ресайз контенту
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 3. Створення квадратного полотна (білий фон)
        new_img = Image.new("RGB", (target_size, target_size), (255, 255, 255))
        
        # 4. Вставка зображення по центру (або зверху-зліва - тут краще зверху-зліва для простішої математики)
        # Але Qwen краще розуміє центр. Давайте вставимо у верхній лівий кут (0,0),
        # це зменшить ризик галюцинацій координат у порожньому просторі.
        paste_x = 0
        paste_y = 0
        new_img.paste(img_resized, (paste_x, paste_y))
        
        # Зберігаємо
        output_buffer = io.BytesIO()
        new_img.save(output_buffer, format="JPEG", quality=95)
        
        # Повертаємо інфо про те, яку частину квадрата займає реальне зображення
        # (x_offset, y_offset, scaled_w, scaled_h)
        padding_info = (paste_x, paste_y, new_w, new_h)
        
        return output_buffer.getvalue(), padding_info, (orig_w, orig_h)

def encode_image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

def extract_json_from_text(text: str) -> Dict[str, Any]:
    # (Тут залишається твій код із "розумним" закриттям дужок, який ми робили в минулому кроці)
    # ...
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match: text = json_match.group(1)
    
    start_idx = text.find('{')
    if start_idx != -1: text = text[start_idx:]
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    text = text.strip()
    open_braces = text.count('{')
    close_braces = text.count('}')
    open_brackets = text.count('[')
    close_brackets = text.count(']')
    
    while open_braces > close_braces:
        text += '}'
        close_braces += 1
    while open_brackets > close_brackets:
        text += ']'
        close_brackets += 1
        
    try:
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        return json.loads(text)
    except:
        return {"error": "Failed to parse JSON", "raw_text": text}

def convert_padded_bbox_to_gradio(
    bbox: List[int], 
    padding_info: Tuple[int, int, int, int],
    original_size: Tuple[int, int],
    canvas_size: int = 1280
) -> List[int]:
    """
    Складна математика:
    1. Переводимо нормалізовані координати (0-1000) у пікселі квадрата (0-1280).
    2. Віднімаємо offset (якщо є).
    3. Перевіряємо, чи точка всередині реального зображення.
    4. Масштабуємо назад до оригінального розміру.
    """
    if not bbox or len(bbox) != 4:
        return None
    
    xmin_norm, ymin_norm, xmax_norm, ymax_norm = bbox
    paste_x, paste_y, scaled_w, scaled_h = padding_info
    orig_w, orig_h = original_size
    
    def transform_coord(c_norm, offset, scaled_dim, orig_dim):
        # 1. Norm (0-1000) -> Canvas Pixel (0-1280)
        c_canvas = (c_norm / 1000.0) * canvas_size
        
        # 2. Canvas Pixel -> Content Pixel (віднімаємо відступ)
        c_content = c_canvas - offset
        
        # 3. Нормалізуємо відносно розміру контенту (0.0 - 1.0)
        # Захист від ділення на нуль та виходу за межі
        if scaled_dim == 0: return 0
        ratio = c_content / scaled_dim
        
        # Обрізаємо межі (clamp)
        ratio = max(0.0, min(1.0, ratio))
        
        # 4. Content Ratio -> Original Pixel
        return int(ratio * orig_dim)

    x1 = transform_coord(min(xmin_norm, xmax_norm), paste_x, scaled_w, orig_w)
    y1 = transform_coord(min(ymin_norm, ymax_norm), paste_y, scaled_h, orig_h)
    x2 = transform_coord(max(xmin_norm, xmax_norm), paste_x, scaled_w, orig_w)
    y2 = transform_coord(max(ymin_norm, ymax_norm), paste_y, scaled_h, orig_h)
    
    return [x1, y1, x2, y2]

def draw_boxes_on_image(
    image: Image.Image,
    json_data: dict,
    padding_info: tuple,
    orig_size: tuple,
    canvas_size: int = 1280
) -> Image.Image:
    """
    Малює рамки прямо на зображенні (backend rendering).
    Це вирішує проблему з fullscreen у Gradio.
    """
    # Робимо копію, щоб не псувати оригінал в пам'яті
    draw_img = image.copy()
    draw = ImageDraw.Draw(draw_img)
    
    # Спробуємо завантажити шрифт, інакше дефолтний
    try:
        # Можна вказати шлях до arial.ttf або іншого шрифту
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()

    if "elements" in json_data and isinstance(json_data["elements"], list):
        for item in json_data["elements"]:
            item_type = item.get("type")
            bbox = item.get("bbox")
            
            # Малюємо тільки значення (Value)
            if item_type == "value" and bbox:
                # Конвертуємо координати
                coords = convert_padded_bbox_to_gradio(
                    bbox, padding_info, orig_size, canvas_size
                )
                
                if coords:
                    x1, y1, x2, y2 = coords
                    
                    # 1. Малюємо напівпрозору підкладку (опціонально)
                    # overlay = Image.new('RGBA', draw_img.size, (0,0,0,0))
                    # draw_overlay = ImageDraw.Draw(overlay)
                    # draw_overlay.rectangle([x1, y1, x2, y2], fill=(0, 255, 0, 40))
                    # draw_img = Image.alpha_composite(draw_img.convert('RGBA'), overlay).convert('RGB')
                    # draw = ImageDraw.Draw(draw_img) # Оновлюємо draw об'єкт

                    # 2. Малюємо рамку (Outline)
                    # Зелений колір #00ff00, товщина 3px
                    draw.rectangle([x1, y1, x2, y2], outline="#00aa00", width=3)
                    
                    # 3. (Опціонально) Можна додати текст зверху, якщо треба
                    # text = item.get("content", "")[:20]
                    # draw.text((x1, y1 - 15), text, fill="red", font=font)

    return draw_img