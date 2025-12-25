# 📄 AI Document Digitizer (Qwen3-VL)

An intelligent document processing API & UI powered by the **Qwen3-VL** multimodal model. It extracts structured data from scanned forms, invoices, and documents, ignoring boilerplate text and focusing on business values.

## 🚀 Features

- **Strict Data Extraction:** Ignores legal text and instructions, extracts only values.
- **Smart Formatting:** Converts tables and forms into structured JSON.
- **Visual Verification:** Interactive UI highlights extracted fields on the image.
- **Multiple Exports:** Download results as JSON, CSV, or Excel.
- **Dual Mode:** Works as a Web UI (Gradio) and a REST API (FastAPI) simultaneously.

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/ituvtu/qwen-doc-parser.git](https://github.com/ituvtu/qwen-doc-parser.git)
   cd qwen-doc-parser
    ```
2. Сreate a virtual environment and install dependencies:
    ```bash
    python -m venv .venv
    # Windows:
    .venv\\Scripts\\activate
    # Mac/Linux:
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
3. Set up environment variables: Copy .env.example to .env and add your Hugging Face Token:
    ```bash 
    HF_TOKEN=your_token_here
    ```
4. ▶️ Usage

    **Run with Docker (Recommended)**
    
    Option A: Using .env file (Best for security)
    ```bash
    docker build -t qwen-doc-parser .
    docker run -p 7860:7860 --env-file .env qwen-doc-parser
    ```
    Option B: Passing token directly
    ```bash
    docker run -p 7860:7860 -e HF_TOKEN=hf_YourTokenHere qwen-doc-parser
    ```
    **Run Locally**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
    ```
    Open your browser at http://localhost:7860.
## 📡 API Example

You can use the API to extract data programmatically:
```bash
curl -X POST "http://localhost:7860/api/v1/extract" \\
     -H "accept: application/json" \\
     -H "Content-Type: multipart/form-data" \\
     -F "file=@/path/to/invoice.jpg"
```
### 🧪 Quick Test Script

The project includes a Python script to verify the API functionality immediately.

1. Open `test_api.py` and update the `IMAGE_PATH` variable to point to your test image.
2. Run the script:
   ```bash
   python test_api.py
   ```