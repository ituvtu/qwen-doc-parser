import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings:
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    
    HF_API_URL: str = "https://router.huggingface.co/v1/chat/completions"
    
    MODEL_ID: str = "Qwen/Qwen3-VL-8B-Instruct:novita"
    
    BACKUP_API_URL: str = os.getenv("BACKUP_API_URL", "")
    MAX_RETRIES: int = 3
    TIMEOUT: int = 120

@lru_cache()
def get_settings() -> Settings:
    return Settings()