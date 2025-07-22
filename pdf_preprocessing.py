"""
pdf_preprocessing.py

PDF content abstraction utilities for robust, schema-driven extraction.
Mirrors the Excel abstraction pipeline (preprocess, summarize, enhance).
"""
import re
from typing import List, Dict, Any

def preprocess_pdf_content(raw_content: str) -> str:
    """
    Preprocess raw PDF content to make it more suitable for LLM extraction.
    Splits into pages if possible, cleans up, and joins.
    """
    if not raw_content:
        return raw_content
    # Try to split by page markers or form feeds
    pages = re.split(r'\f|(?i)--- page:? ?(\d+) ---', raw_content)
    # Remove empty or whitespace-only pages
    processed_pages = [p.strip() for p in pages if p and p.strip()]
    # Optionally, further clean up each page (remove excessive whitespace, etc.)
    return '\n\n'.join(processed_pages)

def generate_pdf_content_summary(raw_content: str) -> str:
    """
    Generate a summary of PDF content to help guide the LLM extraction.
    """
    if not raw_content:
        return "CONTENT SUMMARY: Empty content provided."
    # Try to split into pages
    pages = re.split(r'\f|(?i)--- page:? ?(\d+) ---', raw_content)
    if not pages or len(pages) < 2:
        pages = [raw_content]
    page_summaries = []
    for i, page in enumerate(pages):
        if not page or not page.strip():
            continue
        lines = page.split('\n')
        non_empty_lines = len([line for line in lines if line.strip()])
        financial_indicators = ['total', 'balance', 'profit', 'loss', 'asset', 'liability', 'equity', 'revenue', 'expense', 'cash', 'depreciation']
        found_indicators = [indicator for indicator in financial_indicators if indicator.lower() in page.lower()]
        indicators_text = f", financial indicators found: {', '.join(found_indicators)}" if found_indicators else ""
        page_summaries.append(f"Page {i+1}: {non_empty_lines} non-empty lines{indicators_text}")
    summary = "CONTENT SUMMARY:\n" + "\n".join(page_summaries)
    return summary

def extract_table_structure_from_pdf(raw_content: str) -> List[Dict[str, Any]]:
    """
    Attempt to extract table-like structures from PDF text (simple heuristic).
    """
    tables = []
    # Look for lines with multiple columns (tab or multiple spaces)
    lines = raw_content.split('\n')
    table = []
    for line in lines:
        if re.search(r'\t|  +', line):
            table.append(line)
        else:
            if table:
                tables.append({'lines': table.copy(), 'num_rows': len(table), 'header': table[0] if table else '', 'sample': table[1] if len(table) > 1 else ''})
                table = []
    if table:
        tables.append({'lines': table.copy(), 'num_rows': len(table), 'header': table[0] if table else '', 'sample': table[1] if len(table) > 1 else ''})
    # Optionally, add page or section info
    return tables

def enhance_pdf_extraction(raw_content: str, target_schema: Dict[str, Any]) -> str:
    """
    Enhance PDF content specifically for extraction with a given schema.
    Mirrors the Excel enhancement pipeline.
    """
    processed_content = preprocess_pdf_content(raw_content)
    summary = generate_pdf_content_summary(raw_content)
    tables = extract_table_structure_from_pdf(raw_content)
    table_insights = ""
    if tables:
        table_insights = "TABLE INSIGHTS:\n"
        for i, table in enumerate(tables):
            table_insights += f"Table #{i+1}: {table['num_rows']} rows\n"
            table_insights += f"Header: {table['header']}\n"
            table_insights += f"Sample: {table['sample']}\n\n"
    schema_hints = "EXTRACTION HINTS:\n"
    if any(key in target_schema for key in ['company_name', 'report_period', 'report_date']):
        schema_hints += "- Look for company name and report period at the top of each page\n"
    if any(key in str(target_schema).lower() for key in ['balance', 'asset', 'liability']):
        schema_hints += "- For balance sheet data: Look for 'assets', 'liabilities', and 'equity' sections\n"
    if any(key in str(target_schema).lower() for key in ['profit', 'loss', 'revenue', 'expense']):
        schema_hints += "- For profit & loss data: Look for 'revenue', 'sales', 'cost', 'expense' sections\n"
    if any(key in str(target_schema).lower() for key in ['manufacturing', 'production', 'raw material']):
        schema_hints += "- For manufacturing data: Look for 'raw materials', 'direct labor', 'factory overheads' sections\n"
    enhanced_content = f"{summary}\n\n{table_insights}\n{schema_hints}\n\n{processed_content}"
    return enhanced_content
