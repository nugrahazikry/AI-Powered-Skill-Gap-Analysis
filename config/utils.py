from schemas.pipeline_state import PipelineState
import os
import pdfplumber
import fitz  # pymupdf
from google import genai
from google.genai import types as genai_types
import config.constants as constants


def _ocr_pdf_with_gemini(path: str) -> str:
    """Fallback: render each PDF page as an image and ask Gemini to extract all text."""
    print("WARN: pdfplumber returned no text; falling back to Gemini vision OCR.")
    doc = fitz.open(path)
    image_parts = []
    for page in doc:
        # Render at 150 DPI (zoom=2 ≈ 144 DPI) — good balance of quality vs token cost
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        image_parts.append(
            genai_types.Part.from_bytes(data=png_bytes, mime_type="image/png")
        )
    doc.close()

    if not image_parts:
        return ""

    ocr_prompt = (
        "You are an OCR assistant. Extract ALL text from the CV image(s) below exactly as written. "
        "Preserve the original layout: use line breaks between sections, keep names, dates, "
        "company names, and all details verbatim. Do NOT summarise or reformat — just extract raw text."
    )
    response = constants.CLIENT.models.generate_content(
        model=constants.MODEL_NAME,
        contents=[ocr_prompt, *image_parts],
    )
    return response.text or ""


def read_file_node(state: PipelineState):
    path = state.get("input_path")
    if not path:
        return {}

    if path.lower().endswith(".pdf"):
        # pdfplumber with raised x_tolerance merges spaced-character PDFs correctly
        with pdfplumber.open(path) as pdf:
            pages_text = []
            for page in pdf.pages:
                t = page.extract_text(x_tolerance=5, y_tolerance=5)
                if t:
                    pages_text.append(t)
        text = "\n".join(pages_text)

        # Fallback: if pdfplumber extracted nothing, use Gemini vision OCR
        if not text.strip():
            text = _ocr_pdf_with_gemini(path)
    else:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

    print("INFO: File read successfully.")
    return {"input_text": text}

def pdf_to_txt(pdf_path, target_dir):
    # Make sure target directory exists
    os.makedirs(target_dir, exist_ok=True)

    # Extract filename without extension
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_path = os.path.join(target_dir, f"{base_name}.txt")

    # Extract text from PDF
    with pdfplumber.open(pdf_path) as pdf:
        all_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"

    # Save to target directory
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(all_text)

    print(f"INFO: PDF converted and saved to: {txt_path}")