import pytest
import io
from PIL import Image

@pytest.fixture
def valid_image_bytes():
    """Generates a simple red 100x100 image in memory."""
    img = Image.new('RGB', (100, 100), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()

@pytest.fixture
def mock_hf_response():
    """Imitates response from Qwen-VL."""
    return {
        "choices": [
            {
                "message": {
                    "content": "```json\n{\"elements\": [{\"semantic_label\": \"test_key\", \"content\": \"test_val\", \"bbox\": [0,0,100,100], \"type\": \"value\"}]}\n```"
                }
            }
        ]
    }