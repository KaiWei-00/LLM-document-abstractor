import os
from typing import List, Dict, Any
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import tempfile


def pdf_pages_to_images(pdf_path: str, dpi: int = 300) -> List[str]:
    """
    Convert each page of a PDF to a high-resolution image and return the image file paths.
    """
    doc = fitz.open(pdf_path)
    image_paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_page{i+1}.png") as img_file:
            img_file.write(pix.tobytes("png"))
            image_paths.append(img_file.name)
    doc.close()
    return image_paths


def ocr_images(image_paths: List[str], lang: str = "eng") -> List[str]:
    """
    Run OCR on each image and return the extracted text for each page.
    """
    texts = []
    for img_path in image_paths:
        img = Image.open(img_path)
        text = pytesseract.image_to_string(img, lang=lang)
        texts.append(text)
    return texts


def extract_pdf_via_ocr(pdf_path: str, dpi: int = 300, lang: str = "eng") -> List[Dict[str, Any]]:
    """
    Extract structured data from a PDF by converting each page to image, running OCR, and returning page-wise text.
    """
    image_paths = pdf_pages_to_images(pdf_path, dpi=dpi)
    try:
        texts = ocr_images(image_paths, lang=lang)
        page_results = []
        for idx, text in enumerate(texts):
            page_results.append({"page": idx+1, "text": text})
        return page_results
    finally:
        # Clean up temp image files
        for img_path in image_paths:
            try:
                os.remove(img_path)
            except Exception:
                pass
