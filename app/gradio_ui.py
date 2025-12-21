import gradio as gr
import asyncio
from PIL import Image
import io
import traceback
from app.services.inference import InferenceService
from app.utils.processing import convert_padded_bbox_to_gradio
# Імпорт функцій експорту
from app.utils.export import save_json_file, save_csv_file, save_excel_file

inference_service = InferenceService()

# --- 1. Логіка аналізу ---
async def analyze_document(image):
    if image is None: return None, None, None, None, None # +3 None для кнопок

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    image_bytes = img_byte_arr.getvalue()

    try:
        result = await inference_service.process_document(image_bytes)
        if result is None: return None, {"error": "No result"}, None, None, None
        
        raw_json = result["json"]
        padding_info = result["padding_info"]
        orig_size = result["orig_size"]
        
    except Exception as e:
        traceback.print_exc()
        return None, {"error": str(e)}, None, None, None

    annotations = []
    
    if "elements" in raw_json and isinstance(raw_json["elements"], list):
        for item in raw_json["elements"]:
            bbox = item.get("bbox")
            content = item.get("content", "")
            
            if bbox:
                coords = convert_padded_bbox_to_gradio(
                    bbox, padding_info, orig_size, canvas_size=1280
                )
                label = content[:30] + "..." if len(content) > 30 else content
                annotations.append((coords, label))
    
    # --- ГЕНЕРАЦІЯ ФАЙЛІВ ДЛЯ ЗАВАНТАЖЕННЯ ---
    # Ми генеруємо файли одразу після успішного аналізу
    json_path = save_json_file(raw_json)
    csv_path = save_csv_file(raw_json)
    xlsx_path = save_excel_file(raw_json)

    # Повертаємо: Картинку, JSON, і 3 файли (оновлюємо значення кнопок)
    return (image, annotations), raw_json, json_path, csv_path, xlsx_path

def process_wrapper(image):
    return asyncio.run(analyze_document(image))

# --- 2. Логіка очищення ---
def reset_outputs():
    # Очищаємо все: картинку, json і приховуємо файли (None)
    return None, None, None, None, None

# --- 3. UI ---
theme = gr.themes.Soft(
    primary_hue="blue",
    neutral_hue="slate",
).set(
    body_background_fill="#F9FAFB", 
    block_background_fill="#FFFFFF", 
    block_border_width="1px",
    block_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1)"
)

custom_css = """
button[aria-label="Fullscreen"] {display: none !important;}
"""

with gr.Blocks(title="AI Document Digitizer", theme=theme, css=custom_css) as demo:
    
    with gr.Row():
        gr.Markdown(
            """
            # 📄 AI Document Digitizer
            **Extract structured data from scanned forms instantly.**
            """
        )

    with gr.Row():
        # Ліва колонка
        with gr.Column(scale=1):
            input_img = gr.Image(
                type="pil", 
                label="Upload Document", 
                height=600,
                sources=["upload", "clipboard"]
            )
            
            btn = gr.Button("🚀 Extract Data", variant="primary", size="lg")
            
            # Блок кнопок експорту (з'являться після аналізу)
            with gr.Row():
                btn_json = gr.DownloadButton("📥 JSON", visible=True) 
                btn_csv = gr.DownloadButton("📊 CSV", visible=True)
                btn_excel = gr.DownloadButton("📗 Excel", visible=True)
        
        # Права колонка
        with gr.Column(scale=1):
            output_img = gr.AnnotatedImage(
                label="Interactive Verification",
                height=600,
                color_map={"value": "#22c55e"} 
            )
            
            with gr.Accordion("Raw JSON Output", open=False): 
                output_json = gr.JSON(label="Structured Data")

    # --- ЗВ'ЯЗКИ (Події) ---
    # Функція тепер повертає 5 значень: [Image, JSON, File1, File2, File3]
    btn.click(
        fn=process_wrapper, 
        inputs=input_img, 
        outputs=[output_img, output_json, btn_json, btn_csv, btn_excel]
    )
    
    input_img.change(
        fn=reset_outputs, 
        inputs=None, 
        outputs=[output_img, output_json, btn_json, btn_csv, btn_excel]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860,
        # css=custom_css # розкоментуйте, якщо потрібно для вашої версії
    )