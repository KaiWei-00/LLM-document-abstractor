"""
This script repairs extraction results by directly reading from debug output files
when the extraction result is empty.

This is a temporary fix for the issue where the extraction service processes Excel files
correctly but returns empty extraction results.
"""

import os
import json
import glob
from typing import Dict, Any, Optional


def load_debug_output(debug_folder: str = "debug_output") -> Dict[str, Any]:
    """Load all debug output files and combine into one data structure"""
    result = {}
    
    # Get all text files in the debug folder
    debug_files = glob.glob(os.path.join(debug_folder, "*.txt"))
    print(f"Found {len(debug_files)} debug files in {debug_folder}")
    
    for file_path in debug_files:
        # Get sheet name from filename
        filename = os.path.basename(file_path)
        sheet_name = filename.replace("_raw.txt", "").replace("_", " ")
        
        try:
            print(f"Processing {file_path}...")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            print(f"Content length: {len(content)} characters")
            
            # Try using our custom JSON parser from robust_json.py
            try:
                from robust_json import parse_llm_json
                data = parse_llm_json(content)
                if data:
                    result[sheet_name] = data
                    print(f"Successfully parsed JSON from {filename} using robust parser")
                    continue
            except ImportError:
                print("robust_json module not available, falling back to manual parsing")
            except Exception as e:
                print(f"Error with robust parser: {str(e)}")
            
            # Try standard JSON parsing
            try:
                # Clean up the content - remove any leading/trailing whitespace
                clean_content = content.strip()
                # If it doesn't start with {, find the first {
                if not clean_content.startswith('{'):
                    start_idx = clean_content.find('{')
                    if start_idx >= 0:
                        clean_content = clean_content[start_idx:]
                # If it doesn't end with }, find the last }
                if not clean_content.endswith('}'):
                    end_idx = clean_content.rfind('}')
                    if end_idx >= 0:
                        clean_content = clean_content[:end_idx+1]
                
                # Direct JSON parsing
                data = json.loads(clean_content)
                result[sheet_name] = data
                print(f"Successfully parsed JSON from {filename} after cleanup")
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {str(e)}")
                # Try to find JSON using regex
                import re
                json_match = re.search(r'\{[\s\S]*?\}(?=\s*$|\s*\{)', content)
                if json_match:
                    try:
                        json_content = json_match.group(0)
                        print(f"Found JSON pattern: {json_content[:100]}...")
                        data = json.loads(json_content)
                        result[sheet_name] = data
                        print(f"Successfully extracted JSON using regex from {filename}")
                    except json.JSONDecodeError as e2:
                        print(f"Failed to parse regex match: {str(e2)}")
                        # Last attempt: try to manually fix common JSON issues
                        try:
                            # Replace single quotes with double quotes
                            fixed_content = json_content.replace('\'', '"')
                            # Remove trailing commas before closing brackets
                            fixed_content = re.sub(r',\s*([\]\}])', r'\1', fixed_content)
                            data = json.loads(fixed_content)
                            result[sheet_name] = data
                            print(f"Successfully parsed JSON after manual fixes")
                        except json.JSONDecodeError:
                            print(f"All parsing attempts failed for {filename}")
                else:
                    print(f"No JSON pattern found in {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            print(f"First 100 chars: {content[:100] if content else 'empty'}")
            
    # Create metadata
    if result:
        result["_metadata"] = {
            "sheets": list(result.keys()),
            "sheet_count": len(result),
            "extraction_status": "success" if len(result) > 0 else "error",
            "note": "Data reconstructed from debug files"
        }
        
    return result


def repair_extraction_result(result_file: str) -> Optional[Dict[str, Any]]:
    """Repair an extraction result JSON file by adding data from debug files"""
    try:
        # First check if the result file exists and is valid JSON
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                try:
                    result_data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Original result file contains invalid JSON: {str(e)}")
                    # Create a basic structure if we can't parse the original
                    result_data = {
                        "extracted_data": {},
                        "processing_metadata": {
                            "file_name": os.path.basename(result_file).replace("_", " ").split("_")[0],
                            "repair_timestamp": os.path.getmtime(result_file)
                        }
                    }
        except FileNotFoundError:
            print(f"Result file not found: {result_file}")
            return None
            
        # Check if extracted_data is empty
        if not result_data.get("extracted_data") or len(result_data.get("extracted_data", {})) == 0:
            print(f"Found empty extraction data in {result_file}, attempting repair")
            
            # Load data from debug output
            debug_data = load_debug_output()
            
            if debug_data and len(debug_data) > 0:
                # Make a copy of the result data to avoid modification issues
                repaired_data = result_data.copy()
                
                # Update the extraction result
                repaired_data["extracted_data"] = debug_data
                repaired_data["repair_note"] = "Data restored from debug files"
                
                # Generate a new filename for the repaired result to avoid overwriting
                repaired_file = result_file.replace(".json", "_repaired.json")
                
                # Save the repaired result
                try:
                    with open(repaired_file, "w", encoding="utf-8") as f:
                        json.dump(repaired_data, f, indent=2, ensure_ascii=False)
                    print(f"Repaired extraction result saved to {repaired_file}")
                    
                    # Verify the saved file is valid JSON
                    try:
                        with open(repaired_file, "r", encoding="utf-8") as f:
                            json.load(f)
                        print("Verification successful - saved JSON is valid")
                    except json.JSONDecodeError as e:
                        print(f"WARNING: Saved file contains invalid JSON: {str(e)}")
                except Exception as e:
                    print(f"Error writing repaired file: {str(e)}")
                
                # Print statistics about the repaired data
                sheet_names = [name for name in debug_data.keys() if name != "_metadata"]
                print(f"Repaired data contains {len(sheet_names)} sheets: {', '.join(sheet_names)}")
                
                return repaired_data
            else:
                print("No debug data found to repair with")
        else:
            print(f"Extraction data already exists in {result_file}, no repair needed")
            
        return result_data
    except Exception as e:
        print(f"Error repairing extraction result: {str(e)}")
        return None


if __name__ == "__main__":
    # Find the most recent extraction result
    result_files = glob.glob(os.path.join("extraction_results", "*.json"))
    if result_files:
        # Sort by modification time to get the most recent
        result_files.sort(key=os.path.getmtime, reverse=True)
        latest_result = result_files[0]
        print(f"Repairing most recent result: {latest_result}")
        repaired = repair_extraction_result(latest_result)
        
        if repaired:
            print(f"Repair successful. Extraction now has {len(repaired.get('extracted_data', {}))} sheets")
        else:
            print("Repair failed or was not needed")
    else:
        print("No extraction results found to repair")
