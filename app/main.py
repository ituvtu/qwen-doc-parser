from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import gradio as gr
from app.services.inference import InferenceService
from app.gradio_ui import demo as gradio_app  # Імпортуємо твій існуючий UI

app = FastAPI(title="Qwen-VL Document Extractor API")
service = InferenceService()

# --- API ENDPOINT ---
@app.post("/api/v1/extract")
async def extract_data(file: UploadFile = File(...)):
    """
    Приймає файл зображення (JPEG/PNG).
    Повертає структурований JSON з даними.
    """
    # Перевірка формату
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG/PNG allowed.")

    try:
        # Читаємо байти
        image_bytes = await file.read()
        
        # Відправляємо в сервіс
        result = await service.process_document(image_bytes)
        
        # Якщо сервіс повернув None або помилку
        if not result:
            raise HTTPException(status_code=500, detail="Processing failed")
            
        # Повертаємо чистий JSON (без padding_info, бо API-клієнту це зазвичай не треба)
        return JSONResponse(content=result["json"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- MOUNT GRADIO (UI) ---
# Це дозволяє UI працювати на тому ж порті, що і API
app = gr.mount_gradio_app(app, gradio_app, path="/")

# Для запуску через python main.py (опціонально)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)