import os
import sys
import pytest
from main2 import extract_pdf_page_by_page, DocumentProcessingState

def test_pdf_page_by_page_real():
    # Path to the real PDF file
    pdf_path = os.path.join(os.path.dirname(__file__), '..', 'ABCD Tax Comp.pdf')
    assert os.path.exists(pdf_path), f"Test PDF file not found: {pdf_path}"
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    state = DocumentProcessingState(
        file_content=pdf_bytes,
        file_type='pdf',
        file_name='ABCD Tax Comp.pdf',
        extraction_schema={"dummy": "Dummy schema"},
        error=None,
        processing_stage="content_extracted"
    )
    out_state = extract_pdf_page_by_page(state)
    assert out_state.error is None, f"Extraction error: {out_state.error}"
    assert out_state.extracted_data is not None
    assert "pages" in out_state.extracted_data
    print("Extracted page results:")
    for page in out_state.extracted_data["pages"]:
        print(page)
    # Also check output file
    assert out_state.result_file is not None
    assert os.path.exists(out_state.result_file)
    print(f"Result saved to: {out_state.result_file}")
