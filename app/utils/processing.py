import io
import base64
import re
import json
from typing import Tuple, Dict, Any, List
from PIL import Image, ImageEnhance
import json_repair


def resize_image_smart(image_bytes: bytes, max_side: int = 1280) -> Tuple[bytes, Tuple[int, int], Image.Image]:
    """Resize image preserving aspect ratio, pad to make dimensions divisible by 28,
    and slightly enhance sharpness for better OCR.

    Returns:
        Tuple of (jpeg_bytes, (width, height), final_image).
    """
    with Image.open(io.BytesIO(image_bytes)) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')

        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)

        orig_w, orig_h = img.size

        scale = min(1.0, max_side / max(orig_w, orig_h))
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        canvas_w = ((new_w + 27) // 28) * 28
        canvas_h = ((new_h + 27) // 28) * 28

        final_img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        final_img.paste(img_resized, (0, 0))

        output_buffer = io.BytesIO()
        final_img.save(output_buffer, format="JPEG", quality=95)

        return output_buffer.getvalue(), (canvas_w, canvas_h), final_img


def encode_image_to_base64(image_bytes: bytes) -> str:
    """Encode image bytes to a base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract and repair JSON found in text. Supports fenced ```json blocks."""
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    try:
        decoded_obj = json_repair.loads(text)
        if isinstance(decoded_obj, dict):
            return decoded_obj
        elif isinstance(decoded_obj, list):
            return {"elements": decoded_obj}
        return {"elements": [], "error": "Not a JSON object", "raw_text": text}
    except Exception as e:
        return {"elements": [], "error": str(e), "raw_text": text}


def convert_bbox_to_pixel(bbox: List[int], actual_size: Tuple[int, int]) -> List[int]:
    """Convert bounding box coordinates from 0-1000 scale to pixel coordinates.

    Args:
        bbox: [xmin, ymin, xmax, ymax] in 0-1000 coordinate space.
        actual_size: (width, height) of the image (including padding).

    Returns:
        [x1, y1, x2, y2] in pixels, or None for invalid input.
    """
    if not bbox or len(bbox) != 4:
        return None

    xmin, ymin, xmax, ymax = bbox
    w, h = actual_size

    x1 = int((xmin / 1000.0) * w)
    y1 = int((ymin / 1000.0) * h)
    x2 = int((xmax / 1000.0) * w)
    y2 = int((ymax / 1000.0) * h)

    return [x1, y1, x2, y2]