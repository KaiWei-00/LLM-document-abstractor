"""AI-Powered Excel Document Understanding and Extraction Service.
This module provides intelligent extraction capabilities for Excel documents using AI document understanding,
similar to the PDF processing workflow. Uses ChatGPT for data abstraction and schema-based extraction.
"""
import os
import json
import pandas as pd
import numpy as np
import re
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Import AI components
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI LLM for Excel processing
try:
    # Force use of chat model for Excel processing
    model_name = "gpt-3.5-turbo"  # Always use chat model for Excel
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required for Excel AI processing")
        
    excel_llm = ChatOpenAI(
        model=model_name,
        temperature=0,
        openai_api_key=api_key
    )
    print(f"Excel AI processing initialized with model: {model_name}")
except Exception as e:
    print(f"Warning: Failed to initialize Excel AI processing: {e}")
    excel_llm = None


def describe_schema(schema, indent=0):
    """
    Recursively describe a (possibly nested) schema as a readable string for LLM prompts.
    Supports dicts, lists, and flat fields.
    """
    description = ""
    prefix = "  " * indent
    
    if isinstance(schema, dict):
        for key, value in schema.items():
            if isinstance(value, dict):
                description += f"{prefix}- {key}: (nested object)\n"
                description += describe_schema(value, indent + 1)
            elif isinstance(value, list):
                description += f"{prefix}- {key}: (array)\n"
            else:
                description += f"{prefix}- {key}: {value}\n"
    elif isinstance(schema, list):
        description += f"{prefix}(array of items)\n"
    else:
        description += f"{prefix}{schema}\n"
    
    return description


def ai_excel_document_understanding(sheets_data: Dict[str, str], filename: str) -> Dict[str, Any]:
    """
    AI-powered Excel document understanding that analyzes sheet content intelligently
    and creates a comprehensive document summary and key insights.
    
    Args:
        sheets_data: Dictionary with sheet names as keys and sheet content as values
        filename: Original filename of the Excel file
    
    Returns:
        Dictionary containing document analysis results
    """
    if not excel_llm:
        print("Warning: Excel LLM not initialized, falling back to basic analysis")
        return {
            "overview": f"Basic analysis of {filename} with {len(sheets_data)} sheets",
            "sections": list(sheets_data.keys()),
            "critical_info": {"sheets": list(sheets_data.keys())},
            "document_type": "excel_document",
            "confidence": 0.5
        }
    
    try:
        # Create overview of all sheets
        overview = create_excel_document_overview(sheets_data, filename)
        
        # Identify key sections across sheets
        sections = identify_excel_key_sections(sheets_data)
        
        # Extract critical information using AI understanding
        critical_info = extract_excel_critical_information(sheets_data, overview)
        
        # Determine document type using AI
        document_type = determine_excel_document_type_ai(overview)
        
        # Calculate confidence score
        confidence = calculate_excel_analysis_confidence(overview, sections, critical_info)
        
        return {
            "overview": overview,
            "sections": sections,
            "critical_info": critical_info,
            "document_type": document_type,
            "confidence": confidence
        }
    
    except Exception as e:
        print(f"Error in AI Excel document understanding: {e}")
        return {
            "overview": f"Error analyzing {filename}: {str(e)}",
            "sections": list(sheets_data.keys()),
            "critical_info": {"error": str(e)},
            "document_type": "unknown",
            "confidence": 0.1
        }


def create_excel_document_overview(sheets_data: Dict[str, str], filename: str) -> str:
    """
    Create a comprehensive overview of the Excel document using AI analysis.
    
    Args:
        sheets_data: Dictionary with sheet names and content
        filename: Original filename
    
    Returns:
        String containing document overview
    """
    # Prepare sheet summaries for AI analysis
    sheet_summaries = []
    for sheet_name, content in sheets_data.items():
        # Take first 1000 characters of each sheet for overview
        content_sample = content[:1000] if len(content) > 1000 else content
        sheet_summaries.append(f"Sheet '{sheet_name}': {content_sample}")
    
    combined_content = "\n\n".join(sheet_summaries)
    
    prompt = f"""
    Analyze this Excel document and provide a comprehensive overview.
    
    Document: {filename}
    Number of sheets: {len(sheets_data)}
    Sheet names: {', '.join(sheets_data.keys())}
    
    Content samples from each sheet:
    {combined_content}
    
    Please provide:
    1. Document purpose and type (financial statements, reports, data analysis, etc.)
    2. Key data patterns and structure across sheets
    3. Relationships between sheets (if any)
    4. Primary business/financial information contained
    5. Data quality and completeness assessment
    
    Provide a detailed but concise overview in 3-4 paragraphs.
    """
    
    try:
        messages = [
            SystemMessage(content="You are an expert document analyst specializing in Excel financial and business documents."),
            HumanMessage(content=prompt)
        ]
        
        response = excel_llm.invoke(messages)
        return response.content
    
    except Exception as e:
        print(f"Error creating Excel document overview: {e}")
        return f"Overview of {filename} with {len(sheets_data)} sheets: {', '.join(sheets_data.keys())}"


def identify_excel_key_sections(sheets_data: Dict[str, str]) -> List[str]:
    """
    Identify and categorize key sections across all Excel sheets.
    
    Args:
        sheets_data: Dictionary with sheet names and content
    
    Returns:
        List of identified key sections
    """
    try:
        # Prepare content for AI analysis
        sections_content = ""
        for sheet_name, content in sheets_data.items():
            # Extract headers and key patterns from each sheet
            lines = content.split('\n')[:50]  # First 50 lines for section identification
            sections_content += f"\n--- {sheet_name} ---\n" + "\n".join(lines)
        
        prompt = f"""
        Analyze these Excel sheets and identify key sections and data categories.
        
        Content:
        {sections_content}
        
        Please identify:
        1. Financial statement sections (if any): Balance Sheet items, P&L items, Cash Flow, etc.
        2. Data categories: Headers, totals, calculations, raw data, summaries
        3. Business sections: Revenue, expenses, assets, liabilities, etc.
        4. Structural elements: Tables, charts references, formulas
        
        Return a simple list of the main sections/categories found, one per line.
        """
        
        messages = [
            SystemMessage(content="You are an expert at analyzing Excel document structure and identifying key sections."),
            HumanMessage(content=prompt)
        ]
        
        response = excel_llm.invoke(messages)
        # Parse response into list
        sections = [line.strip() for line in response.content.split('\n') if line.strip() and not line.startswith('#')]
        return sections[:20]  # Limit to top 20 sections
    
    except Exception as e:
        print(f"Error identifying Excel key sections: {e}")
        return list(sheets_data.keys())  # Fallback to sheet names


def extract_excel_critical_information(sheets_data: Dict[str, str], overview: str) -> Dict[str, Any]:
    """
    Extract critical information using AI understanding of the Excel document context.
    
    Args:
        sheets_data: Dictionary with sheet names and content
        overview: Document overview from previous analysis
    
    Returns:
        Dictionary containing critical information
    """
    try:
        # Combine all sheet content for comprehensive analysis
        all_content = ""
        for sheet_name, content in sheets_data.items():
            all_content += f"\n\n=== SHEET: {sheet_name} ===\n{content}"
        
        # Limit content size for API
        if len(all_content) > 8000:
            all_content = all_content[:8000] + "\n... (content truncated)"
        
        prompt = f"""
        Based on the document overview and content, extract the most critical business information.
        
        Document Overview:
        {overview}
        
        Full Content:
        {all_content}
        
        Please extract and return as JSON:
        {{
            "company_info": {{
                "name": "company name if found",
                "period": "reporting period if found"
            }},
            "financial_highlights": {{
                "key_figures": ["list of important numbers with labels"],
                "totals": ["significant totals found"]
            }},
            "data_structure": {{
                "primary_sheets": ["most important sheet names"],
                "data_types": ["types of data found"]
            }},
            "quality_indicators": {{
                "completeness": "assessment of data completeness",
                "consistency": "assessment of data consistency"
            }}
        }}
        
        Return only valid JSON.
        """
        
        messages = [
            SystemMessage(content="You are an expert at extracting critical business information from Excel documents. Always return valid JSON."),
            HumanMessage(content=prompt)
        ]
        
        response = excel_llm.invoke(messages)
        
        # Parse JSON response
        try:
            critical_info = json.loads(response.content)
            return critical_info
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                return {"raw_analysis": response.content}
    
    except Exception as e:
        print(f"Error extracting Excel critical information: {e}")
        return {
            "error": str(e),
            "sheets": list(sheets_data.keys()),
            "sheet_count": len(sheets_data)
        }


def determine_excel_document_type_ai(overview: str) -> str:
    """
    Use AI to determine the specific Excel document type based on overview.
    
    Args:
        overview: Document overview from analysis
    
    Returns:
        String indicating document type
    """
    try:
        prompt = f"""
        Based on this document overview, determine the specific document type.
        
        Overview:
        {overview}
        
        Choose the most appropriate type from:
        - balance_sheet
        - profit_loss_statement
        - manufacturing_account
        - financial_statements
        - budget_report
        - sales_report
        - inventory_report
        - general_ledger
        - trial_balance
        - cash_flow_statement
        - management_accounts
        - other_business_document
        
        Return only the document type, nothing else.
        """
        
        messages = [
            SystemMessage(content="You are an expert at classifying business and financial documents."),
            HumanMessage(content=prompt)
        ]
        
        response = excel_llm.invoke(messages)
        return response.content.strip().lower()
    
    except Exception as e:
        print(f"Error determining Excel document type: {e}")
        return "unknown_excel_document"


def calculate_excel_analysis_confidence(overview: str, sections: List[str], critical_info: Dict[str, Any]) -> float:
    """
    Calculate confidence score for the Excel AI analysis.
    
    Args:
        overview: Document overview
        sections: Identified sections
        critical_info: Extracted critical information
    
    Returns:
        Float confidence score between 0 and 1
    """
    try:
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on overview quality
        if overview and len(overview) > 100:
            confidence += 0.2
        
        # Boost confidence based on sections identified
        if sections and len(sections) >= 3:
            confidence += 0.1
        
        # Boost confidence based on critical info extracted
        if critical_info and isinstance(critical_info, dict):
            if len(critical_info) >= 3:
                confidence += 0.1
            if "company_info" in critical_info:
                confidence += 0.05
            if "financial_highlights" in critical_info:
                confidence += 0.05
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    except Exception as e:
        print(f"Error calculating Excel analysis confidence: {e}")
        return 0.3  # Low confidence fallback


def ai_excel_schema_based_extraction(document_analysis: Dict[str, Any], schema: Dict[str, Any], schema_description: str, sheets_data: Dict[str, str]) -> Dict[str, Any]:
    """
    Use AI understanding to apply the detected schema and generate structured JSON output for Excel.
    
    Args:
        document_analysis: Results from AI document understanding
        schema: The detected/provided schema to apply
        schema_description: Human-readable description of the schema
        sheets_data: Original sheet data
    
    Returns:
        Dictionary containing structured extraction results
    """
    if not excel_llm:
        print("Warning: Excel LLM not initialized for schema-based extraction")
        return {"error": "AI extraction not available"}
    
    try:
        # Process each sheet individually to get better extraction results
        sheet_results = {}
        
        for sheet_name, sheet_content in sheets_data.items():
            print(f"Processing sheet: {sheet_name}")
            
            # Limit content size for API
            content_to_process = sheet_content
            if len(content_to_process) > 8000:
                content_to_process = content_to_process[:8000] + "\n... (content truncated for processing)"
            
            prompt = f"""
            Extract structured data from this Excel sheet using the provided schema and document understanding.
            
            SHEET NAME: {sheet_name}
            
            DOCUMENT ANALYSIS:
            - Type: {document_analysis.get('document_type', 'unknown')}
            - Overview: {document_analysis.get('overview', 'No overview available')}
            - Key Sections: {', '.join(document_analysis.get('sections', []))}
            
            EXTRACTION SCHEMA:
            {schema_description}
            
            SCHEMA STRUCTURE:
            {describe_schema(schema)}
            
            SHEET CONTENT:
            {content_to_process}
            
            INSTRUCTIONS:
            1. Extract data from this specific sheet: {sheet_name}
            2. Use the document analysis to understand the context
            3. Apply the most appropriate schema based on sheet content
            4. In Excel, field names and values may be in different cells - scan horizontally and vertically
            5. Preserve financial formatting (currency symbols, decimals)
            6. Return only valid JSON with the extracted data
            7. If a field is not found, use empty string or null
            8. Focus on the actual data values, not headers
            
            Return the extracted data as valid JSON.
            """
            
            messages = [
                SystemMessage(content=f"You are an expert at extracting structured data from Excel sheets. Focus on extracting data from the '{sheet_name}' sheet. Always return valid JSON."),
                HumanMessage(content=prompt)
            ]
            
            try:
                response = excel_llm.invoke(messages)
                
                # Parse JSON response
                try:
                    sheet_data = json.loads(response.content)
                    sheet_results[sheet_name] = sheet_data
                    print(f"Successfully extracted data from {sheet_name}")
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                    if json_match:
                        try:
                            sheet_data = json.loads(json_match.group(0))
                            sheet_results[sheet_name] = sheet_data
                            print(f"Successfully extracted data from {sheet_name} (with JSON cleanup)")
                        except json.JSONDecodeError:
                            sheet_results[sheet_name] = {
                                "extraction_error": "Failed to parse AI response as JSON",
                                "raw_response": response.content[:300]
                            }
                    else:
                        sheet_results[sheet_name] = {
                            "extraction_error": "No valid JSON found in response",
                            "raw_response": response.content[:300]
                        }
                        
            except Exception as sheet_error:
                print(f"Error processing sheet {sheet_name}: {sheet_error}")
                sheet_results[sheet_name] = {
                    "extraction_error": f"Error processing sheet: {str(sheet_error)}",
                    "sheet_name": sheet_name
                }
        
        return sheet_results
    
    except Exception as e:
        print(f"Error in AI Excel schema-based extraction: {e}")
        return {
            "extraction_error": str(e),
            "document_type": document_analysis.get('document_type', 'unknown')
        }


# For robust JSON parsing
def parse_json(text):
    """Simple JSON parsing with error handling"""
    try:
        return json.loads(text)
    except Exception as e:
        print(f"JSON parsing error: {str(e)}")
        return {}

# Note: clean_value and old extraction functions removed - now using AI-powered extraction


def extract_balance_sheet(df: pd.DataFrame) -> Dict:
    """
    Extract balance sheet data from DataFrame.
    
    Args:
        df: Pandas DataFrame containing balance sheet data
        
    Returns:
        Dictionary with structured balance sheet data
    """
    # Basic structure matching the schema definition
    balance_sheet = {
        "company_name": "",
        "report_date": "",
        "non_current_assets": {
            "property_plant_equipment": "",
            "investments": "",
            "total": ""
        },
        "current_assets": {
            "inventory": "",
            "trade_receivables": "",
            "cash_equivalents": "",
            "total": ""
        },
        "current_liabilities": {
            "trade_payables": "",
            "short_term_loans": "",
            "total": ""
        },
        "non_current_liabilities": {
            "long_term_loans": "",
            "total": ""
        },
        "equity": {
            "share_capital": "",
            "retained_earnings": "",
            "total": ""
        },
        "total_assets": "",
        "total_liabilities_equity": ""
    }
    
    # Try to find company name and report date
    for i in range(min(5, len(df))):
        row = df.iloc[i] if i < len(df) else None
        if row is None:
            continue
            
        row_text = ' '.join([str(val).lower() for val in row.values if pd.notna(val)])
        
        # Look for company name patterns
        if 'ltd' in row_text or 'limited' in row_text or 'llc' in row_text or 'inc' in row_text:
            balance_sheet["company_name"] = next((str(val) for val in row.values if pd.notna(val)), "")
        
        # Look for date patterns
        date_pattern = r'\b(?:as at|as of|at|date[d]?:?)\s+([a-zA-Z0-9\s,]+\d{4})\b'
        date_match = re.search(date_pattern, row_text, re.IGNORECASE)
        if date_match:
            balance_sheet["report_date"] = date_match.group(1).strip()
            
    # Process the data rows to extract assets and liabilities based on new schema structure
    non_current_assets_section = False
    current_assets_section = False
    current_liabilities_section = False
    non_current_liabilities_section = False
    equity_section = False
    
    # Extract financial data
    for i in range(len(df)):
        row = df.iloc[i]
        first_col = str(row.iloc[0]).lower() if not pd.isna(row.iloc[0]) else ""
        
        # Skip empty rows
        if first_col.strip() == "":
            continue
            
        # Check which section we're in
        if 'non-current assets' in first_col or 'fixed assets' in first_col or 'property, plant' in first_col:
            non_current_assets_section = True
            current_assets_section = False
            current_liabilities_section = False
            non_current_liabilities_section = False
            equity_section = False
            continue
            
        if 'current assets' in first_col:
            non_current_assets_section = False
            current_assets_section = True
            current_liabilities_section = False
            non_current_liabilities_section = False
            equity_section = False
            continue
            
        if 'current liabilities' in first_col:
            non_current_assets_section = False
            current_assets_section = False
            current_liabilities_section = True
            non_current_liabilities_section = False
            equity_section = False
            continue
            
        if 'non-current liabilities' in first_col or 'long term liabilities' in first_col:
            non_current_assets_section = False
            current_assets_section = False
            current_liabilities_section = False
            non_current_liabilities_section = True
            equity_section = False
            continue
            
        if 'equity' in first_col or 'capital' in first_col or 'shareholders' in first_col:
            non_current_assets_section = False
            current_assets_section = False
            current_liabilities_section = False
            non_current_liabilities_section = False
            equity_section = True
            continue
        
        # Extract values based on current section
        value = clean_value(row.iloc[-1]) if len(row) > 1 else ""
        
        if non_current_assets_section:
            if 'property' in first_col or 'plant' in first_col or 'equipment' in first_col:
                balance_sheet["non_current_assets"]["property_plant_equipment"] = value
            elif 'investment' in first_col:
                balance_sheet["non_current_assets"]["investments"] = value
            elif 'total' in first_col:
                balance_sheet["non_current_assets"]["total"] = value
                
        elif current_assets_section:
            if 'inventory' in first_col or 'stock' in first_col:
                balance_sheet["current_assets"]["inventory"] = value
            elif 'receivable' in first_col or 'debtor' in first_col:
                balance_sheet["current_assets"]["trade_receivables"] = value
            elif 'cash' in first_col or 'bank' in first_col:
                balance_sheet["current_assets"]["cash_equivalents"] = value
            elif 'total' in first_col:
                balance_sheet["current_assets"]["total"] = value
                
        elif current_liabilities_section:
            if 'payable' in first_col or 'creditor' in first_col or 'trade' in first_col:
                balance_sheet["current_liabilities"]["trade_payables"] = value
            elif 'loan' in first_col or 'borrowing' in first_col:
                balance_sheet["current_liabilities"]["short_term_loans"] = value
            elif 'total' in first_col:
                balance_sheet["current_liabilities"]["total"] = value
                
        elif non_current_liabilities_section:
            if 'loan' in first_col or 'borrowing' in first_col or 'debt' in first_col:
                balance_sheet["non_current_liabilities"]["long_term_loans"] = value
            elif 'total' in first_col:
                balance_sheet["non_current_liabilities"]["total"] = value
                
        elif equity_section:
            if 'share' in first_col or 'capital' in first_col:
                balance_sheet["equity"]["share_capital"] = value
            elif 'retain' in first_col or 'earning' in first_col or 'reserve' in first_col:
                balance_sheet["equity"]["retained_earnings"] = value
            elif 'total' in first_col:
                balance_sheet["equity"]["total"] = value
                
        # Check for total assets and total liabilities & equity
        if 'total assets' in first_col:
            balance_sheet["total_assets"] = value
        elif ('total liabilities' in first_col and 'equity' in first_col) or 'total equity and liabilities' in first_col:
            balance_sheet["total_liabilities_equity"] = value
                
    return balance_sheet


def extract_profit_loss(df: pd.DataFrame) -> Dict:
    """
    Extract profit and loss data from DataFrame.
    
    Args:
        df: Pandas DataFrame containing profit and loss data
        
    Returns:
        Dictionary with structured profit and loss data
    """
    # Basic structure matching the schema definition
    profit_loss = {
        "company_name": "",
        "report_period": "",
        "revenue": "",
        "cost_of_sales": {
            "opening_stock": "",
            "manufacturing_cost": "",
            "purchases": "",
            "closing_stock": "",
            "total": ""
        },
        "gross_profit": "",
        "other_income": {
            "interest_income": "",
            "misc_income": "",
            "total": ""
        },
        "expenses": {
            "administrative": "",
            "selling": "",
            "financial": "",
            "total": ""
        },
        "net_profit": ""
    }
    
    # Try to find company name and report date
    for i in range(min(5, len(df))):
        row = df.iloc[i] if i < len(df) else None
        if row is None:
            continue
            
        row_text = ' '.join([str(val).lower() for val in row.values if pd.notna(val)])
        
        # Look for company name patterns
        if 'ltd' in row_text or 'limited' in row_text or 'llc' in row_text or 'inc' in row_text:
            profit_loss["company_name"] = next((str(val) for val in row.values if pd.notna(val)), "")
        
        # Look for date patterns
        period_pattern = r'\b(?:for|period|year)(?:\s+(?:end|ended|ending))?\s+([a-zA-Z0-9\s,]+\d{4})\b'
        period_match = re.search(period_pattern, row_text, re.IGNORECASE)
        if period_match:
            profit_loss["report_period"] = period_match.group(1).strip()
    
    # Process the data rows
    revenue_section = False
    expenses_section = False
    profit_section = False
    
    for i in range(len(df)):
        row = df.iloc[i]
        first_col = str(row.iloc[0]).lower() if not pd.isna(row.iloc[0]) else ""
        
        # Determine which section we're in
        if any(term in first_col for term in ['revenue', 'sales', 'turnover', 'income']):
            revenue_section = True
            expenses_section = False
            profit_section = False
        elif any(term in first_col for term in ['cost', 'expense', 'expenditure']):
            revenue_section = False
            expenses_section = True
            profit_section = False
        elif any(term in first_col for term in ['profit', 'loss', 'earnings']):
            revenue_section = False
            expenses_section = False
            profit_section = True
        
        # Skip empty rows
        if first_col.strip() == "":
            continue
        
        # Extract values
        value = clean_value(row.iloc[-1]) if len(row) > 1 else ""
        
        if revenue_section:
            if 'total' in first_col:
                profit_loss["total_revenue"] = value
            else:
                profit_loss["revenue"][first_col] = value
        elif expenses_section:
            if 'total' in first_col:
                profit_loss["total_expenses"] = value
            else:
                profit_loss["expenses"][first_col] = value
        elif profit_section:
            if 'gross' in first_col:
                profit_loss["gross_profit"] = value
            elif 'operating' in first_col:
                profit_loss["operating_profit"] = value
            elif 'net' in first_col or ('profit' in first_col and 'after' in first_col):
                profit_loss["net_profit"] = value
    
    return profit_loss


def extract_manufacturing_account(df: pd.DataFrame) -> Dict:
    """
    Extract manufacturing account data from DataFrame.
    
    Args:
        df: Pandas DataFrame containing manufacturing account data
        
    Returns:
        Dictionary with structured manufacturing data
    """
    manufacturing = {
        "company_name": "",
        "report_period": "",
        "raw_material": {
            "opening_stock": "",
            "purchases": "",
            "returns_outwards": "",
            "closing_stock": "",
            "cost_of_raw_material_consumed": ""
        },
        "direct_labour": {
            "bonus": "",
            "casual_wages": "",
            "epf": "",
            "socso": "",
            "eis": "",
            "sub_contract_wages": "",
            "wages_salaries": "",
            "total": ""
        },
        "factory_overheads": {
            "depreciation": "",
            "factory_expenses": "",
            "total_overheads": ""
        },
        "total_cost": "",
        "work_in_progress": {
            "opening": "",
            "closing": ""
        },
        "production_cost": ""
    }
    
    # Try to find company name and report period
    for i in range(min(5, len(df))):
        row = df.iloc[i] if i < len(df) else None
        if row is None:
            continue
            
        row_text = ' '.join([str(val).lower() for val in row.values if pd.notna(val)])
        
        # Look for company name patterns
        if 'ltd' in row_text or 'limited' in row_text or 'llc' in row_text or 'inc' in row_text:
            manufacturing["company_name"] = next((str(val) for val in row.values if pd.notna(val)), "")
        
        # Look for period patterns
        period_pattern = r'\b(?:for|period|year)(?:\s+(?:end|ended|ending))?\s+([a-zA-Z0-9\s,]+\d{4})\b'
        period_match = re.search(period_pattern, row_text, re.IGNORECASE)
        if period_match:
            manufacturing["report_period"] = period_match.group(1).strip()
    
    # Process rows to extract manufacturing data
    raw_materials_section = False
    labor_section = False
    overheads_section = False
    wip_section = False
    finished_goods_section = False
    
    for i in range(len(df)):
        row = df.iloc[i]
        first_col = str(row.iloc[0]).lower() if not pd.isna(row.iloc[0]) else ""
        
        # Determine which section we're in
        if any(term in first_col for term in ['raw material', 'materials']):
            raw_materials_section = True
            labor_section = False
            overheads_section = False
            wip_section = False
            finished_goods_section = False
        elif any(term in first_col for term in ['direct labor', 'labour', 'wages']):
            raw_materials_section = False
            labor_section = True
            overheads_section = False
            wip_section = False
            finished_goods_section = False
        elif any(term in first_col for term in ['factory overhead', 'manufacturing overhead']):
            raw_materials_section = False
            labor_section = False
            overheads_section = True
            wip_section = False
            finished_goods_section = False
        elif any(term in first_col for term in ['work in progress', 'wip']):
            raw_materials_section = False
            labor_section = False
            overheads_section = False
            wip_section = True
            finished_goods_section = False
        elif any(term in first_col for term in ['finished goods', 'finished product']):
            raw_materials_section = False
            labor_section = False
            overheads_section = False
            wip_section = False
            finished_goods_section = True
            
        # Skip empty rows
        if first_col.strip() == "":
            continue
            
        # Extract values
        value = clean_value(row.iloc[-1]) if len(row) > 1 else ""
        
        if raw_materials_section:
            if 'opening' in first_col or 'beginning' in first_col:
                manufacturing["raw_materials"]["opening_stock"] = value
            elif 'purchase' in first_col:
                manufacturing["raw_materials"]["purchases"] = value
            elif 'closing' in first_col or 'ending' in first_col:
                manufacturing["raw_materials"]["closing_stock"] = value
        elif labor_section:
            manufacturing["direct_labor"][first_col] = value
        elif overheads_section:
            manufacturing["factory_overheads"][first_col] = value
        elif wip_section:
            if 'opening' in first_col or 'beginning' in first_col:
                manufacturing["work_in_progress"]["opening"] = value
            elif 'closing' in first_col or 'ending' in first_col:
                manufacturing["work_in_progress"]["closing"] = value
        elif finished_goods_section:
            if 'opening' in first_col or 'beginning' in first_col:
                manufacturing["finished_goods"]["opening_stock"] = value
            elif 'closing' in first_col or 'ending' in first_col:
                manufacturing["finished_goods"]["closing_stock"] = value
                
        # Check for cost of production and cost of goods sold
        if 'cost of production' in first_col:
            manufacturing["cost_of_production"] = value
        elif 'cost of goods sold' in first_col or 'cogs' in first_col:
            manufacturing["cost_of_goods_sold"] = value
    
    return manufacturing


def fix_excel_extraction(file_path: str, original_filename: str) -> Dict[str, Any]:
    """
    AI-powered Excel extraction using document understanding and schema-based extraction.
    Replaces hardcoded extraction logic with intelligent AI analysis.
    
    Args:
        file_path: Path to the Excel file
        original_filename: Original filename of the Excel file
        
    Returns:
        A dictionary containing extracted financial data in structured format
    """
    print(f"Applying AI-powered Excel extraction for: {original_filename}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_time = datetime.now()
    
    # Create debug directory
    debug_dir = "debug_output"
    os.makedirs(debug_dir, exist_ok=True)
    
    try:
        # Step 1: Read Excel file and extract sheet content
        print("Step 1: Reading Excel sheets...")
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        sheets_data = {}
        
        for sheet_name in sheet_names:
            try:
                # Read with safety limits
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=1000)
                if not df.empty:
                    # Convert DataFrame to text representation for AI analysis
                    sheet_text = df.to_string(max_rows=200, max_cols=20)
                    sheets_data[sheet_name] = sheet_text
                    print(f"Loaded sheet: {sheet_name} ({len(df)} rows)")
            except Exception as e:
                print(f"Error reading sheet {sheet_name}: {str(e)}")
                continue
        
        if not sheets_data:
            raise Exception("No readable sheets found in Excel file")
        
        # Step 2: AI Document Understanding
        print("Step 2: Performing AI document understanding...")
        document_analysis = ai_excel_document_understanding(sheets_data, original_filename)
        
        # Step 3: Create a comprehensive schema based on document analysis
        print("Step 3: Creating comprehensive schema...")
        # Use a comprehensive financial schema that covers all possible sheet types
        comprehensive_schema = {
            "Balance Sheet": {
                "company_name": "string",
                "report_date": "string",
                "non_current_assets": {
                    "property_plant_equipment": "number",
                    "investments": "number",
                    "intangible_assets": "number",
                    "other_assets": "number",
                    "total": "number"
                },
                "current_assets": {
                    "inventory": "number",
                    "trade_receivables": "number",
                    "cash_equivalents": "number",
                    "other_current_assets": "number",
                    "total": "number"
                },
                "total_assets": "number",
                "current_liabilities": {
                    "trade_payables": "number",
                    "short_term_borrowings": "number",
                    "accruals": "number",
                    "other_current_liabilities": "number",
                    "total": "number"
                },
                "non_current_liabilities": {
                    "long_term_borrowings": "number",
                    "deferred_tax": "number",
                    "other_non_current_liabilities": "number",
                    "total": "number"
                },
                "equity": {
                    "share_capital": "number",
                    "retained_earnings": "number",
                    "other_reserves": "number",
                    "total": "number"
                },
                "total_liabilities_equity": "number"
            },
            "Trading P&L": {
                "company_name": "string",
                "report_period": "string",
                "revenue": "number",
                "cost_of_sales": {
                    "opening_stock": "number",
                    "manufacturing_cost": "number",
                    "purchases": "number",
                    "closing_stock": "number",
                    "total": "number"
                },
                "gross_profit": "number",
                "other_income": {
                    "interest_income": "number",
                    "misc_income": "number",
                    "total": "number"
                },
                "expenses": {
                    "administrative": "number",
                    "selling_distribution": "number",
                    "financial": "number",
                    "other_expenses": "number",
                    "total": "number"
                },
                "operating_profit": "number",
                "net_profit": "number"
            },
            "Manufacturing Account": {
                "company_name": "string",
                "report_period": "string",
                "raw_material": {
                    "opening_stock": "number",
                    "purchases": "number",
                    "returns_outwards": "number",
                    "closing_stock": "number",
                    "cost_of_raw_material_consumed": "number"
                },
                "direct_labour": {
                    "wages_salaries": "number",
                    "bonus": "number",
                    "casual_wages": "number",
                    "epf": "number",
                    "socso": "number",
                    "eis": "number",
                    "sub_contract_wages": "number",
                    "total": "number"
                },
                "factory_overheads": {
                    "depreciation": "number",
                    "factory_expenses": "number",
                    "utilities": "number",
                    "maintenance": "number",
                    "total_overheads": "number"
                },
                "total_cost": "number",
                "work_in_progress": {
                    "opening": "number",
                    "closing": "number"
                },
                "production_cost": "number"
            }
        }
        
        schema_description = describe_schema(comprehensive_schema)
        
        # Step 4: AI Schema-Based Extraction
        print("Step 4: Performing AI schema-based extraction...")
        extraction_results = ai_excel_schema_based_extraction(
            document_analysis, 
            comprehensive_schema, 
            schema_description, 
            sheets_data
        )
        
        # Step 5: Build final result structure
        processing_time = (datetime.now() - start_time).total_seconds()
        successful_sheets = list(extraction_results.get("extracted_data", {}).keys())
        
        final_result = {
            # Extract sheet data to top level
            **extraction_results.get("extracted_data", {}),
            # Add metadata
            "_metadata": {
                "sheets": successful_sheets,
                "successful_sheets": successful_sheets,
                "sheet_count": len(successful_sheets),
                "successful_count": len(successful_sheets),
                "extraction_status": "success" if successful_sheets else "failure",
                "timestamp": datetime.now().isoformat(),
                "file_processed": original_filename,
                "note": "Data extracted using AI-powered document understanding",
                "ai_analysis": {
                    "document_type": document_analysis.get("document_type", "unknown"),
                    "confidence": document_analysis.get("confidence", 0),
                    "key_sections": document_analysis.get("key_sections", [])
                }
            },
            "schema_detection": {
                "detected_schema_type": "comprehensive_financial",
                "confidence_score": document_analysis.get("confidence", 0.8),
                "reasoning": f"AI analysis identified document as {document_analysis.get('document_type', 'financial document')}"
            },
            "processing_metadata": {
                "file_name": original_filename,
                "file_type": "excel",
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat(),
                "debug_files": os.path.abspath(debug_dir),
                "ai_powered": True,
                "extraction_method": "ai_document_understanding"
            }
        }
        
        print(f"AI extraction completed successfully. Found {len(successful_sheets)} sheets.")
        
    except Exception as e:
        print(f"Error in AI-powered Excel extraction for {original_filename}: {str(e)}")
        traceback.print_exc()
        
        # Fallback result structure
        final_result = {
            "_metadata": {
                "sheets": [],
                "successful_sheets": [],
                "sheet_count": 0,
                "successful_count": 0,
                "extraction_status": "failure",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "file_processed": original_filename,
                "note": "AI extraction failed, no fallback data available"
            },
            "schema_detection": {
                "detected_schema_type": "unknown",
                "confidence_score": 0,
                "reasoning": "AI extraction failed"
            },
            "processing_metadata": {
                "file_name": original_filename,
                "file_type": "excel",
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat(),
                "debug_files": os.path.abspath(debug_dir),
                "ai_powered": True,
                "extraction_method": "ai_document_understanding",
                "error": str(e)
            }
        }
    
    # Save the full result for debugging
    try:
        debug_file = os.path.join(debug_dir, f"{Path(original_filename).stem}_ai_extraction_{timestamp}.json")
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)
        print(f"Saved AI extraction result to {debug_file}")
    except Exception as e:
        print(f"Could not save debug file: {str(e)}")
    
    return final_result
