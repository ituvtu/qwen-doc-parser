from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
import uvicorn
import gradio as gr
from loguru import logger

from app.services.inference import InferenceService
from app.gradio_ui import demo as gradio_app
from app.dependencies import get_inference_service

app = FastAPI(title="Qwen-VL Document Extractor API")

@app.post("/api/v1/extract")
async def extract_data(
    file: UploadFile = File(...),

    service: InferenceService = Depends(get_inference_service) 
):
    logger.info(f"API Request: /extract from {file.filename}")

    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        logger.warning(f"Invalid content type: {file.content_type}")
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG/PNG allowed.")

    try:
        image_bytes = await file.read()
        
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        result = await service.process_document(image_bytes)
        
        if not result:
            raise HTTPException(status_code=500, detail="Processing failed")
            
        return JSONResponse(content=result["json"])

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Global API Exception")
        raise HTTPException(status_code=500, detail=str(e))

app = gr.mount_gradio_app(app, gradio_app, path="/")

if __name__ == "__main__":
    logger.info("Starting Server...")
    uvicorn.run(app, host="0.0.0.0", port=7860)