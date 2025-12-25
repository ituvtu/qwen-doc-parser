import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from app.main import app
from app.dependencies import get_inference_service
from app.services.inference import InferenceService

client = TestClient(app)

@pytest.fixture
def mock_openai_response():
    mock_response = MagicMock()
    mock_message = MagicMock()

    mock_message.content = '''```json
    {"elements": [{"semantic_label": "test_key", "content": "test_val", "bbox": [0,0,100,100]}]}
    ```'''
    
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    
    mock_response.choices = [mock_choice]
    return mock_response

@pytest.mark.asyncio
async def test_api_integration_flow(valid_image_bytes, mock_openai_response):
    """
    The correct test for FastAPI + OpenAI SDK.
    We use dependency_overrides to replace the real service
    with a version with a mock OpenAI client.
    """
    
    service = InferenceService()
    service.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)

    app.dependency_overrides[get_inference_service] = lambda: service

    try:
        from httpx import AsyncClient, ASGITransport

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            files = {'file': ('test.jpg', valid_image_bytes, 'image/jpeg')}
            response = await ac.post("/api/v1/extract", files=files)

            assert response.status_code == 200
            
            data = response.json()
            assert "elements" in data
            assert len(data["elements"]) > 0
            assert data["elements"][0]["content"] == "test_val"
            
            service.client.chat.completions.create.assert_called_once()

    finally:
        app.dependency_overrides = {}

def test_api_rejects_bad_files():
    """We are verifying that the API rejects text files."""
    files = {'file': ('test.txt', b'some text', 'text/plain')}
    response = client.post("/api/v1/extract", files=files)
    assert response.status_code == 400

def test_api_handles_corrupted_images():
    """We check that the API does not return a 500 error, but returns a 400 error for broken images."""
    files = {'file': ('test.jpg', b'THIS IS NOT A JPG', 'image/jpeg')}
    response = client.post("/api/v1/extract", files=files)
    assert response.status_code == 400
    assert "Invalid image" in response.json()["detail"]


def test_api_missing_file():
    """Test POST without file parameter."""
    response = client.post("/api/v1/extract")
    assert response.status_code == 422 

def test_api_file_size_limits(valid_image_bytes):
    """Test handling of very large files."""
    huge_file = valid_image_bytes * 10000  
    files = {'file': ('huge.jpg', huge_file, 'image/jpeg')}
    response = client.post("/api/v1/extract", files=files, timeout=2)
    assert response.status_code in [413, 408, 504]