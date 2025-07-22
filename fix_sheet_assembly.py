# Insert this code at the end of handle_large_content_extraction function
# after state.extracted_data = sheet_results and before returning state

# Add a special metadata field to keep track of extraction status
metadata = {
    "extraction_status": "partial" if any(status == "success" for status in sheet_status.values()) else "failed",
    "error": state.error if state.error else None
}

# Ensure extracted_data is a dictionary 
if not isinstance(state.extracted_data, dict):
    state.extracted_data = {}
    
# Add metadata to track status of extraction
state.extracted_data["_metadata"] = metadata

# Debug info
print(f"Extracted data has {len(state.extracted_data.keys())} keys (sheet names)")
for sheet_name in state.extracted_data.keys():
    print(f"Sheet: {sheet_name}")
    if isinstance(state.extracted_data[sheet_name], dict):
        print(f"Sheet {sheet_name} has data: {list(state.extracted_data[sheet_name].keys())}")

# The main issue is likely in the extract_structured_data function
# where we need to ensure we properly merge the sheet data into the final output

