from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    HF_TOKEN: str
    
    HF_BASE_URL: str = "https://router.huggingface.co/v1"
    
    MODEL_ID: str = "Qwen/Qwen3-VL-8B-Instruct:novita"
    
    MAX_RETRIES: int = 3
    TIMEOUT: int = 120

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    return Settings()