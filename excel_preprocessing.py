"""
Excel content preprocessing utilities to improve LLM extraction.
This module helps format Excel content in a way that is more conducive to LLM processing.
"""
import re
import os
from typing import Dict, List, Any, Optional, Tuple, Union

def preprocess_excel_content(raw_content: str) -> str:
    """
    Preprocess raw Excel content to make it more suitable for LLM extraction.
    
    Args:
        raw_content: Raw text content extracted from Excel file
        
    Returns:
        Preprocessed content optimized for LLM extraction
    """
    if not raw_content:
        return raw_content
        
    # Split content into sheets
    sheets = re.split(r"--- Sheet: ([^-]+) ---", raw_content)
    
    # First element is empty if the content starts with a sheet marker
    if sheets and not sheets[0].strip():
        sheets.pop(0)
        
    # Process sheet by sheet
    processed_sheets = []
    
    # Process sheets in pairs (sheet_name, sheet_content)
    for i in range(0, len(sheets), 2):
        if i + 1 >= len(sheets):
            break
            
        sheet_name = sheets[i].strip()
        sheet_content = sheets[i + 1].strip()
        
        # Skip empty sheets
        if not sheet_content:
            continue
            
        # Process sheet content
        processed_content = _process_sheet_content(sheet_content)
        
        # Add to processed sheets
        processed_sheets.append(f"--- Sheet: {sheet_name} ---\n{processed_content}")
        
    # Join processed sheets
    return "\n\n".join(processed_sheets)

def _process_sheet_content(content: str) -> str:
    """Process individual sheet content for better LLM extraction"""
    lines = content.split('\n')
    processed_lines = []
    
    # Find potential headers (first non-empty row)
    header_line = None
    for line in lines:
        if line.strip():
            header_line = line
            break
    
    # Process each line
    current_section = None
    for line in lines:
        line = line.strip()
        
        # Skip excessive empty lines (keep some for structure)
        if not line:
            if processed_lines and not processed_lines[-1]:
                continue
            processed_lines.append(line)
            continue
            
        # Check if this is a header line (all caps or ends with colon)
        if line.isupper() or line.endswith(':'):
            current_section = line
            # Add extra emphasis to section headers
            processed_lines.append(f"### {line} ###")
            continue
            
        # Check if this might be a key-value pair
        if ':' in line:
            processed_lines.append(line)
            continue
            
        # Regular content line
        processed_lines.append(line)
        
    # Join processed lines
    return '\n'.join(processed_lines)

def extract_table_structure(content: str) -> List[Dict[str, Any]]:
    """
    Extract table structure from Excel content.
    
    Args:
        content: Processed Excel content
        
    Returns:
        List of dictionaries representing table structures
    """
    tables = []
    
    # Split content into sheets
    sheets = re.split(r"--- Sheet: ([^-]+) ---", content)
    
    # First element is empty if the content starts with a sheet marker
    if sheets and not sheets[0].strip():
        sheets.pop(0)
        
    # Process sheet by sheet
    for i in range(0, len(sheets), 2):
        if i + 1 >= len(sheets):
            break
            
        sheet_name = sheets[i].strip()
        sheet_content = sheets[i + 1].strip()
        
        # Skip empty sheets
        if not sheet_content:
            continue
            
        # Try to extract table structure
        tables.extend(_extract_tables_from_sheet(sheet_name, sheet_content))
        
    return tables

def _extract_tables_from_sheet(sheet_name: str, content: str) -> List[Dict[str, Any]]:
    """Extract table structures from a single sheet"""
    tables = []
    lines = content.split('\n')
    
    # Look for consecutive non-empty lines that could form tables
    table_start = None
    for i, line in enumerate(lines):
        if not line.strip():
            if table_start is not None:
                # We found the end of a potential table
                table_content = lines[table_start:i]
                if len(table_content) > 2:  # At least a header and one row
                    tables.append({
                        "sheet": sheet_name,
                        "start_line": table_start,
                        "end_line": i - 1,
                        "num_rows": len(table_content),
                        "header": table_content[0],
                        "sample": table_content[1] if len(table_content) > 1 else ""
                    })
                table_start = None
        elif table_start is None:
            # Start of a potential table
            table_start = i
            
    # Handle case where table extends to the end
    if table_start is not None:
        table_content = lines[table_start:]
        if len(table_content) > 2:
            tables.append({
                "sheet": sheet_name,
                "start_line": table_start,
                "end_line": len(lines) - 1,
                "num_rows": len(table_content),
                "header": table_content[0],
                "sample": table_content[1] if len(table_content) > 1 else ""
            })
            
    return tables

def generate_content_summary(raw_content: str) -> str:
    """
    Generate a summary of Excel content to help guide the LLM extraction.
    
    Args:
        raw_content: Raw Excel content
        
    Returns:
        A summary string with content structure insights
    """
    if not raw_content:
        return "CONTENT SUMMARY: Empty content provided."
        
    # Split into sheets
    sheets = re.split(r"--- Sheet: ([^-]+) ---", raw_content)
    
    # Remove empty first element if needed
    if sheets and not sheets[0].strip():
        sheets.pop(0)
        
    if not sheets:
        return "CONTENT SUMMARY: No valid sheet content found."
        
    # Generate sheet-level summaries
    sheet_summaries = []
    
    # Process sheets in pairs (sheet_name, sheet_content)
    for i in range(0, len(sheets), 2):
        if i + 1 >= len(sheets):
            break
            
        sheet_name = sheets[i].strip()
        sheet_content = sheets[i + 1].strip()
        
        # Skip empty sheets
        if not sheet_content:
            sheet_summaries.append(f"Sheet '{sheet_name}': Empty")
            continue
            
        # Count lines and estimate table structures
        lines = sheet_content.split('\n')
        non_empty_lines = len([line for line in lines if line.strip()])
        
        # Look for financial indicators
        financial_indicators = ['total', 'balance', 'profit', 'loss', 'asset', 'liability', 
                               'equity', 'revenue', 'expense', 'cash', 'depreciation']
        found_indicators = []
        
        for indicator in financial_indicators:
            if indicator.lower() in sheet_content.lower():
                found_indicators.append(indicator)
                
        indicators_text = f", financial indicators found: {', '.join(found_indicators)}" if found_indicators else ""
        
        # Add summary for this sheet
        sheet_summaries.append(f"Sheet '{sheet_name}': {non_empty_lines} non-empty lines{indicators_text}")
        
    # Combine into final summary
    summary = "CONTENT SUMMARY:\n" + "\n".join(sheet_summaries)
    return summary

def enhance_excel_extraction(raw_content: str, target_schema: Dict[str, Any]) -> str:
    """
    Enhance Excel content specifically for extraction with a given schema.
    
    Args:
        raw_content: Raw Excel content
        target_schema: Schema to extract
        
    Returns:
        Enhanced content with extraction hints
    """
    # Preprocess the content first
    processed_content = preprocess_excel_content(raw_content)
    
    # Generate a content summary
    summary = generate_content_summary(raw_content)
    
    # Extract potential table structures
    tables = extract_table_structure(raw_content)
    
    # Generate table insight text
    table_insights = ""
    if tables:
        table_insights = "TABLE INSIGHTS:\n"
        for i, table in enumerate(tables):
            table_insights += f"Table #{i+1} in sheet '{table['sheet']}': {table['num_rows']} rows\n"
            table_insights += f"Header: {table['header']}\n"
            table_insights += f"Sample: {table['sample']}\n\n"
    
    # Create extraction hints based on schema and content
    schema_hints = "EXTRACTION HINTS:\n"
    
    # Add hints for common financial document fields
    if any(key in target_schema for key in ['company_name', 'report_period', 'report_date']):
        schema_hints += "- Look for company name and report period at the top of each sheet\n"
    
    if any(key in str(target_schema).lower() for key in ['balance', 'asset', 'liability']):
        schema_hints += "- For balance sheet data: Look for 'assets', 'liabilities', and 'equity' sections\n"
    
    if any(key in str(target_schema).lower() for key in ['profit', 'loss', 'revenue', 'expense']):
        schema_hints += "- For profit & loss data: Look for 'revenue', 'sales', 'cost', 'expense' sections\n"
    
    if any(key in str(target_schema).lower() for key in ['manufacturing', 'production', 'raw material']):
        schema_hints += "- For manufacturing data: Look for 'raw materials', 'direct labor', 'factory overheads' sections\n"
    
    # Combine everything
    enhanced_content = f"{summary}\n\n{table_insights}\n{schema_hints}\n\n{processed_content}"
    return enhanced_content
