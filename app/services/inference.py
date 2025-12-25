from fastapi import HTTPException
from loguru import logger
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings
from app.utils.processing import (
    encode_image_to_base64, 
    extract_json_from_text, 
    resize_image_smart 
)

settings = get_settings()

class InferenceService:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.HF_BASE_URL,
            api_key=settings.HF_TOKEN,
            timeout=settings.TIMEOUT
        )

    async def process_document(self, image_bytes: bytes) -> dict:
        logger.info(f"Processing document size: {len(image_bytes)} bytes")

        try:
            processed_bytes, actual_size, pil_image = resize_image_smart(image_bytes, max_side=1568)
            
            base64_img = encode_image_to_base64(processed_bytes)
            data_uri = f"data:image/jpeg;base64,{base64_img}"
            logger.debug(f"Model input size: {actual_size}")
            
        except Exception as e:
            logger.warning(f"Image decode failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid image file.")
        
        system_instruction = (
            "You are an expert Document Intelligence AI. Your task is to extract structured information.\n\n"
            "INSTRUCTIONS:\n"
            "1. Analyze the document layout accurately.\n"
            "2. Extract text fields strictly as they appear.\n"
            "3. Return accurate Bounding Boxes [ymin, xmin, ymax, xmax] (0-1000 scale) for every element.\n"
            "4. If a field has a label (e.g. 'Date:'), extract only the value ('10/13/99').\n\n"
            "OUTPUT JSON format:\n"
            "{\n"
            '  "elements": [\n'
            '    {"label": "field_name", "content": "extracted text", "bbox": [100, 200, 150, 400]}\n'
            "  ]\n"
            "}"
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_instruction},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }
        ]

        try:
            chat_completion = await self._make_openai_request(messages)
        except Exception as e:
            logger.error(f"LLM Request failed: {e}")
            raise HTTPException(status_code=503, detail=f"Model error: {str(e)}")

        if not chat_completion.choices:
             raise HTTPException(status_code=502, detail="Empty response")

        content = chat_completion.choices[0].message.content
        parsed_json = extract_json_from_text(content)
        
        logger.success("Document processed successfully")
        
        return {
            "json": parsed_json,
            "image_size": actual_size,
            "processed_image": pil_image 
        }

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, APITimeoutError, RateLimitError)),
        reraise=True
    )
    async def _make_openai_request(self, messages: list):
        return await self.client.chat.completions.create(
            model=settings.MODEL_ID,
            messages=messages,
            max_tokens=4096,
            temperature=0.0
        )