import os
import tempfile
from typing import List, Dict, Any
import os
import tempfile
from typing import List, Dict, Any
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

# Set Tesseract path for Windows (adjust if needed)
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_pdf_via_images(pdf_path: str, prompt: str = None, model: str = None) -> List[Dict[str, Any]]:
    """
    Convert each page of a PDF to an image, extract text from each image using Tesseract OCR,
    and return a list of results (one per page).
    """
    results = []
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        try:
            text = pytesseract.image_to_string(image)
            data = {"text": text}
        except Exception as e:
            data = {"error": str(e)}
        results.append({"page": i+1, "data": data})
    return results

def aggregate_page_results(page_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combine results from all pages into a single dictionary or list as needed.
    Also save the combined OCR text to a debug file for inspection.
    """
    combined_text = "\n".join([p["data"].get("text", "") for p in page_results if "data" in p and "text" in p["data"]])
    # Save to debug file
    debug_path = os.path.join(os.getcwd(), "ocr_debug_output.txt")
    try:
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(combined_text)
        print(f"[DEBUG] Saved combined OCR text to {debug_path}")
    except Exception as e:
        print(f"[DEBUG] Failed to save OCR debug output: {e}")
    return {"pages": page_results, "combined_text": combined_text}
