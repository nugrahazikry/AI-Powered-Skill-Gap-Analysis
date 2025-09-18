from schemas.pipeline_state import PipelineState
import os
import pdfplumber

def read_file_node(state: PipelineState):
    path = state.get("input_path")
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    print(f"✅ The file has been read successfully.")
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

    print(f"✅ PDF converted and saved to: {txt_path}")