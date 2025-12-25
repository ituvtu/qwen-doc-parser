import gradio as gr
import io
from loguru import logger
from app.services.inference import InferenceService
from app.utils.processing import convert_bbox_to_pixel
from app.utils.export import save_json_file, save_csv_file, save_excel_file

inference_service = InferenceService()

async def analyze_document(image):
    if image is None: return None, None, None, None, None

    orig_w, orig_h = image.size
    image = image.convert("RGB")

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=95)
    image_bytes = img_byte_arr.getvalue()

    try:
        logger.info(f"User started document analysis. Original size: {orig_w}x{orig_h}")
        result = await inference_service.process_document(image_bytes)
        
        if result is None: 
            return None, {"error": "No result"}, None, None, None
        
        raw_json = result["json"]
        actual_size = result.get("image_size", (orig_w, orig_h))
        processed_pil = result.get("processed_image", image)
        
    except Exception as e:
        logger.exception("Error in Gradio interface") 
        return None, {"error": str(e)}, None, None, None

    annotations = []
    if "elements" in raw_json and isinstance(raw_json["elements"], list):
        for item in raw_json["elements"]:
            bbox = item.get("bbox") or item.get("bbox_2d")
            content = item.get("content") or item.get("text_content") or item.get("text") or item.get("value")
            
            if not content:
                content = item.get("label") or item.get("semantic_label") or "?"

            if bbox:
                coords = convert_bbox_to_pixel(bbox, actual_size)
                label_text = str(content)
                label_short = label_text[:30] + "..." if len(label_text) > 30 else label_text
                annotations.append((coords, label_short))
    
    json_path = save_json_file(raw_json)
    csv_path = save_csv_file(raw_json)
    xlsx_path = save_excel_file(raw_json)

    return (processed_pil, annotations), raw_json, json_path, csv_path, xlsx_path

def reset_outputs():
    return None, None, None, None, None


theme = gr.themes.Soft(primary_hue="blue", neutral_hue="slate").set(
    body_background_fill="#F9FAFB", 
    block_background_fill="#FFFFFF", 
    block_border_width="1px"
)

custom_css = "button[aria-label='Fullscreen'] {display: none !important;}"

with gr.Blocks(title="AI Document Digitizer") as demo:
    with gr.Row():
        gr.Markdown("# 📄 AI Document Digitizer")

    with gr.Row():
        with gr.Column(scale=1):
            input_img = gr.Image(type="pil", label="Upload Document", height=600)
            btn = gr.Button("🚀 Extract Data", variant="primary", size="lg")
            with gr.Row():
                btn_json = gr.DownloadButton("📥 JSON") 
                btn_csv = gr.DownloadButton("📊 CSV")
                btn_excel = gr.DownloadButton("📗 Excel")
        
        with gr.Column(scale=1):
            output_img = gr.AnnotatedImage(label="Verification", height=600, color_map={"value": "#22c55e"})
            with gr.Accordion("Raw JSON Output", open=False): 
                output_json = gr.JSON()

    btn.click(
        fn=analyze_document, 
        inputs=input_img, 
        outputs=[output_img, output_json, btn_json, btn_csv, btn_excel]
    )
    
    input_img.change(
        fn=reset_outputs, 
        inputs=None, 
        outputs=[output_img, output_json, btn_json, btn_csv, btn_excel]
    )

demo.theme = theme
demo.css = custom_css

if __name__ == "__main__":

    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860,
        theme=theme,
        css=custom_css
    )