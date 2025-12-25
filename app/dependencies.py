from functools import lru_cache
from app.services.inference import InferenceService

@lru_cache()
def get_inference_service() -> InferenceService:
    """
    Creates a Singleton service.
    lru_cache ensures that we create the object only once
    and use it for all requests.
    """
    return InferenceService()