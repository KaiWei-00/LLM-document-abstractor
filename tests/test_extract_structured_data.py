import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import json
from pydantic import BaseModel
from main2 import extract_structured_data, DocumentProcessingState

def make_state(content, schema):
    return DocumentProcessingState(
        file_content=content,
        file_type='pdf',
        file_name='test.pdf',
        extraction_schema=schema,
        error=None,
        processing_stage="content_extracted"
    )

# Expected use: valid JSON output
@pytest.mark.parametrize("llm_output,expected", [
    ('{"company_name": "ABC Corp", "revenue": "1000000", "year": "2023"}', {'company_name': 'ABC Corp', 'revenue': '1000000', 'year': '2023'}),
    ('\n{"company_name": "ABC Corp", "revenue": "1000000", "year": "2023"}\n', {'company_name': 'ABC Corp', 'revenue': '1000000', 'year': '2023'}),
    ('Some explanation. {"company_name": "ABC Corp", "revenue": "1000000", "year": "2023"} End.', {'company_name': 'ABC Corp', 'revenue': '1000000', 'year': '2023'}),
    ('{"company_name": "ABC Corp", "revenue": "1000000", "year": "2023",}', {'company_name': 'ABC Corp', 'revenue': '1000000', 'year': '2023'}),
])
def test_extract_structured_data_valid(monkeypatch, llm_output, expected):
    schema = {"company_name": "Name", "revenue": "Revenue", "year": "Year"}
    state = make_state("Sample content", schema)
    class DummyLLM:
        def invoke(self, *a, **kw):
            return llm_output
    monkeypatch.setattr("main2.llm", DummyLLM())
    new_state = extract_structured_data(state)
    assert new_state.error is None
    assert new_state.extracted_data == expected

# Edge case: nested schema
@pytest.mark.parametrize("llm_output,expected", [
    ('{"company_name": "ABC Corp", "raw_material": {"opening_stock": "5000", "purchases": "2000"}}', {'company_name': 'ABC Corp', 'raw_material': {'opening_stock': '5000', 'purchases': '2000'}}),
])
def test_extract_structured_data_nested(monkeypatch, llm_output, expected):
    schema = {"company_name": "Name", "raw_material": {"opening_stock": "Opening", "purchases": "Purchases"}}
    state = make_state("Sample content", schema)
    class DummyLLM:
        def invoke(self, *a, **kw):
            return llm_output
    monkeypatch.setattr("main2.llm", DummyLLM())
    new_state = extract_structured_data(state)
    assert new_state.error is None
    assert new_state.extracted_data == expected

# Failure case: completely invalid JSON
@pytest.mark.parametrize("llm_output", [
    ("Not JSON at all"),
    ("{company_name: 'ABC Corp', revenue: 1000000, year: 2023}"),
    ("[This is not a JSON object]"),
])
def test_extract_structured_data_failure(monkeypatch, llm_output):
    schema = {"company_name": "Name", "revenue": "Revenue", "year": "Year"}
    state = make_state("Sample content", schema)
    class DummyLLM:
        def invoke(self, *a, **kw):
            return llm_output
    monkeypatch.setattr("main2.llm", DummyLLM())
    new_state = extract_structured_data(state)
    assert new_state.error is not None
    assert new_state.extracted_data is None
