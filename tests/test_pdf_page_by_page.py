import sys
import os
import json
import tempfile
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main2 import extract_pdf_page_by_page, DocumentProcessingState

def make_state_from_pages(pages, file_name='test.pdf'):
    # Simulate PDF file content as bytes (not real PDF, just for logic test)
    fake_bytes = b'Fake PDF content for test.'
    return DocumentProcessingState(
        file_content=fake_bytes,
        file_type='pdf',
        file_name=file_name,
        extraction_schema={"dummy": "Dummy schema"},
        error=None,
        processing_stage="content_extracted"
    )

class DummyLLM:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = []
    def invoke(self, messages, max_tokens=None):
        idx = len(self.calls)
        self.calls.append(messages)
        # Return corresponding output or last one
        out = self.outputs[idx] if idx < len(self.outputs) else self.outputs[-1]
        class Resp:
            content = out
        return Resp()

@pytest.mark.parametrize("page_texts,llm_outputs,expected", [  # expected is list of dicts
    (["Page 1 text", "Page 2 text"],
     [json.dumps({"foo": 1}), json.dumps({"bar": 2})],
     [{"page": 1, "data": {"foo": 1}}, {"page": 2, "data": {"bar": 2}}]),
    (["Page 1 text"],
     [json.dumps({"single": True})],
     [{"page": 1, "data": {"single": True}}]),
    ([""],
     [],
     [{"page": 1, "error": "Empty page or extraction failed"}]),
])
def test_pdf_page_by_page(monkeypatch, tmp_path, page_texts, llm_outputs, expected):
    # Patch extract_pdf_pages to return our page_texts
    monkeypatch.setattr("main2.extract_pdf_pages", lambda path: page_texts)
    # Patch llm
    monkeypatch.setattr("main2.llm", DummyLLM(llm_outputs))
    # Patch os.path.dirname to tmp_path for output
    monkeypatch.setattr("main2.os.path.dirname", lambda f: str(tmp_path))
    # Patch time.strftime to fixed value
    monkeypatch.setattr("main2.time.strftime", lambda fmt: "20250101_120000")
    state = make_state_from_pages(page_texts)
    out_state = extract_pdf_page_by_page(state)
    assert out_state.error is None
    assert "pages" in out_state.extracted_data
    # Only check the page-level results
    assert out_state.extracted_data["pages"] == expected
    # Check file written
    out_file = out_state.result_file
    assert os.path.exists(out_file)
    with open(out_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["pages"] == expected

# Edge case: LLM returns invalid JSON
@pytest.mark.parametrize("page_texts,llm_outputs", [
    (["Page 1 text"], ["Not JSON"]),
    (["Page 1 text", "Page 2 text"], ["{invalid}", "{}"]),
])
def test_pdf_page_by_page_invalid_json(monkeypatch, tmp_path, page_texts, llm_outputs):
    monkeypatch.setattr("main2.extract_pdf_pages", lambda path: page_texts)
    monkeypatch.setattr("main2.llm", DummyLLM(llm_outputs))
    monkeypatch.setattr("main2.os.path.dirname", lambda f: str(tmp_path))
    monkeypatch.setattr("main2.time.strftime", lambda fmt: "20250101_120000")
    state = make_state_from_pages(page_texts)
    out_state = extract_pdf_page_by_page(state)
    assert out_state.error is None
    assert "pages" in out_state.extracted_data
    for page in out_state.extracted_data["pages"]:
        if "error" in page:
            assert "Failed to parse JSON" in page["error"] or "Empty page" in page["error"]
