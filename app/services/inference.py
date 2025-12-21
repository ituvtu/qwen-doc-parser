import httpx
import asyncio
from fastapi import HTTPException
from app.config import get_settings
from app.utils.processing import (
    encode_image_to_base64, 
    extract_json_from_text, 
    resize_and_pad_image
)

settings = get_settings()

class InferenceService:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.HF_TOKEN}",
            "Content-Type": "application/json"
        }

    async def process_document(self, image_bytes: bytes) -> dict:
        processed_bytes, padding_info, orig_size = resize_and_pad_image(image_bytes, target_size=1280)
        base64_img = encode_image_to_base64(processed_bytes)
        data_uri = f"data:image/jpeg;base64,{base64_img}"

        # --- ОНОВЛЕНИЙ ЕКОНОМНИЙ ПРОМПТ ---
        system_instruction = (
            "You are a Strict Data Extractor.\n"
            "Task: Extract ONLY the meaningful variable data (values) from the document.\n"
            "CRITICAL RULES (To save tokens):\n"
            "1. IGNORE static form text (labels like 'Name:', 'Date:', 'Page:'). Extract only the VALUE next to them.\n"
            "2. IGNORE boilerplate text, instructions (e.g., 'Please call...', 'Comments'), legal disclaimers, and footers.\n"
            "3. IGNORE empty fields (if a line is blank, do not create an object).\n"
            "4. For Tables: Extract every cell content as a value.\n\n"
            "Output Format: JSON with 'elements' list. Each item:\n"
            "  - 'semantic_label': Short snake_case key (e.g. 'date', 'total', 'row_1_col_2'). Keep it brief.\n"
            "  - 'content': The extracted value text.\n"
            "  - 'bbox': [xmin, ymin, xmax, ymax] (0-1000 scale).\n"
            "  - 'type': 'value'\n"
        )
        # ----------------------------------

        payload = {
            "model": settings.MODEL_ID,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_instruction},
                        {"type": "image_url", "image_url": {"url": data_uri}}
                    ]
                }
            ],
            "max_tokens": 4096,
            "response_format": {"type": "json_object"}, 
            "temperature": 0.0
        }

        try:
            raw_response = await self._make_request_with_retry(
                settings.HF_API_URL, 
                payload
            )
            
            if not raw_response or "choices" not in raw_response:
                 raise HTTPException(status_code=502, detail="Empty response")

            content = raw_response["choices"][0]["message"]["content"]
            parsed_json = extract_json_from_text(content)
            
            return {
                "json": parsed_json,
                "padding_info": padding_info,
                "orig_size": orig_size
            }

        except HTTPException:
            raise
        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _make_request_with_retry(self, url: str, payload: dict) -> dict:
         async with httpx.AsyncClient(timeout=settings.TIMEOUT) as client:
            for attempt in range(settings.MAX_RETRIES):
                try:
                    response = await client.post(url, headers=self.headers, json=payload)
                    if response.status_code == 200: return response.json()
                    if response.status_code == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    if response.status_code >= 500:
                        await asyncio.sleep(2)
                        continue
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                except httpx.RequestError:
                    await asyncio.sleep(1)
            raise HTTPException(status_code=503, detail="Service unavailable")