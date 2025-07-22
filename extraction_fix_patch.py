"""
Patch for the document extraction service to ensure Excel extraction results are properly included
in the API response, even when there are parsing issues with the LLM output.

This patch integrates the repair mechanism into the API endpoint handler to fix the empty
extraction results issue.
"""

import os
import json
import glob
import re
from typing import Dict, Any, Optional


def load_debug_sheet_data(debug_folder: str = "debug_output") -> Dict[str, Any]:
    """
    Load all debug output files and combine into one data structure.
    This is used as a fallback when the normal extraction process fails.
    """
    result = {}
    
    # Get all text files in the debug folder
    debug_files = glob.glob(os.path.join(debug_folder, "*.txt"))
    print(f"Found {len(debug_files)} debug files in {debug_folder}")
    
    for file_path in debug_files:
        # Get sheet name from filename
        filename = os.path.basename(file_path)
        sheet_name = filename.replace("_raw.txt", "").replace("_", " ")
        
        try:
            # Read the file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            # Try to parse the JSON - first with robust_json if available
            try:
                from robust_json import parse_llm_json
                data = parse_llm_json(content)
                if data:
                    result[sheet_name] = data
                    print(f"Successfully parsed debug file for sheet: {sheet_name}")
                    continue
            except ImportError:
                print("robust_json module not available, falling back to standard parsing")
            except Exception as e:
                print(f"Error with robust JSON parser: {str(e)}")
            
            # Try standard JSON parsing with cleanup
            try:
                # Remove any non-JSON content at the start/end
                clean_content = content
                json_start = clean_content.find('{')
                json_end = clean_content.rfind('}')
                
                if json_start >= 0 and json_end > json_start:
                    clean_content = clean_content[json_start:json_end+1]
                    data = json.loads(clean_content)
                    result[sheet_name] = data
                    print(f"Successfully parsed debug file for sheet: {sheet_name}")
                else:
                    print(f"No valid JSON structure found in debug file for sheet: {sheet_name}")
            except json.JSONDecodeError:
                # Try to extract with regex as last resort
                try:
                    json_match = re.search(r'\{[\s\S]*?\}', content)
                    if json_match:
                        data = json.loads(json_match.group(0))
                        result[sheet_name] = data
                        print(f"Successfully extracted JSON with regex for sheet: {sheet_name}")
                except Exception:
                    print(f"Failed to extract valid JSON from debug file for sheet: {sheet_name}")
        except Exception as e:
            print(f"Error processing debug file for sheet {sheet_name}: {str(e)}")
    
    # Add metadata if we found any sheets
    if result:
        sheet_names = list(result.keys())
        result["_metadata"] = {
            "sheets": sheet_names,
            "sheet_count": len(sheet_names),
            "extraction_status": "success" if sheet_names else "error",
            "source": "debug_files"
        }
    
    return result


def ensure_extraction_data(extracted_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ensure we have valid extraction data by checking the debug output files
    when the normal extraction process fails or returns empty results.
    
    Args:
        extracted_data: The extraction data from the normal process, which might be empty
        
    Returns:
        Dictionary with extraction data, either from the normal process or from debug files
    """
    # If we already have good data, just return it
    if extracted_data and isinstance(extracted_data, dict) and len(extracted_data) > 0:
        # Check if we have actual sheet data (not just metadata)
        has_sheet_data = False
        for key, value in extracted_data.items():
            if key != "_metadata" and value and isinstance(value, (dict, list)) and len(value) > 0:
                has_sheet_data = True
                break
        
        if has_sheet_data:
            print("Using existing extraction data (valid sheet data found)")
            return extracted_data
        else:
            print("No valid sheet data found in extraction result, checking debug files...")
    else:
        print("Empty or invalid extraction data, checking debug files...")
    
    # Load data from debug files as a fallback
    debug_data = load_debug_sheet_data()
    
    if debug_data and isinstance(debug_data, dict) and len(debug_data) > 0:
        # Check if we have actual sheet data (not just metadata)
        has_sheet_data = False
        for key, value in debug_data.items():
            if key != "_metadata" and value and isinstance(value, (dict, list)) and len(value) > 0:
                has_sheet_data = True
                break
        
        if has_sheet_data:
            print(f"Using data from debug files: {len(debug_data)} sheets")
            return debug_data
    
    # If we still don't have data, return a minimal structure with an error
    print("No valid data found in extraction or debug files")
    return {
        "_metadata": {
            "extraction_status": "error",
            "error": "No valid data could be extracted"
        }
    }


# To patch the main2.py file, add the following to the extract_document_info endpoint:
"""
# After preparing the extraction_result but before returning the API response

# Check if the extraction_result is empty and try to recover from debug files if needed
if not extraction_result or (isinstance(extraction_result, dict) and len(extraction_result) <= 1 and "_metadata" in extraction_result):
    print("WARNING: Empty extraction result detected, attempting to recover from debug files...")
    from extraction_fix_patch import ensure_extraction_data
    extraction_result = ensure_extraction_data(extraction_result)
    print(f"After recovery: {len(extraction_result.keys() if isinstance(extraction_result, dict) else [])} keys in extraction result")
"""
