import os
import tempfile
import pytest
from main2 import extract_document_content, extract_structured_data, DocumentProcessingState

SAMPLE_PDF_TEXT = (
    "Page 1: Revenue: 1000\nExpense: 500\n\f"
    "Page 2: Revenue: 2000\nExpense: 800\n\f"
    "Page 3: Revenue: 3000\nExpense: 1200\n"
)

@pytest.fixture
def fake_pdf_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='w', encoding='utf-8') as f:
        f.write(SAMPLE_PDF_TEXT)
        yield f.name
    os.unlink(f.name)

def test_pdf_chunking_and_extraction(monkeypatch, fake_pdf_file):
    # Patch extract_pdf_content to just return our sample text
    monkeypatch.setattr('main2.extract_pdf_content', lambda file_path: SAMPLE_PDF_TEXT)
    # Patch extract_with_simplified_prompt to just return chunk summary
    def fake_extract_with_simplified_prompt(state):
        # Simulate extracting numbers from chunk
        import re
        revenue = sum(map(int, re.findall(r'Revenue: (\d+)', state.file_content)))
        expense = sum(map(int, re.findall(r'Expense: (\d+)', state.file_content)))
        state.extracted_data = {'Revenue': str(revenue), 'Expense': str(expense)}
        state.processing_stage = 'data_extracted'
        return state
    monkeypatch.setattr('main2.extract_with_simplified_prompt', fake_extract_with_simplified_prompt)
    # Patch merge_nested_dicts to just merge sums
    def fake_merge_nested_dicts(d1, d2):
        out = dict(d1)
        for k, v in d2.items():
            out[k] = str(int(out.get(k, '0')) + int(v))
        return out
    monkeypatch.setattr('main2.merge_nested_dicts', fake_merge_nested_dicts)

    # Simulate pipeline
    # Provide file_content as the extracted text (simulate what extract_pdf_content returns)
    state = DocumentProcessingState(
        file_content=SAMPLE_PDF_TEXT,
        file_type='pdf',
        file_name='sample.pdf',
        extraction_schema={'Revenue': '', 'Expense': ''}
    )
    state = extract_document_content(state)
    assert hasattr(state, 'pdf_chunks')
    assert len(state.pdf_chunks) == 3
    state = extract_structured_data(state)
    assert state.extracted_data['Revenue'] == '6000'
    assert state.extracted_data['Expense'] == '2500'
