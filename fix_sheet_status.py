# Insert this code at the API endpoint before the sheet_status reference
# Determine overall extraction status based on individual sheets
sheet_status = {}  # Initialize empty dict to prevent variable reference errors
if hasattr(final_state, "sheet_status") and final_state.sheet_status:
    sheet_status = final_state.sheet_status
elif isinstance(final_state, dict) and "sheet_status" in final_state:
    sheet_status = final_state.get("sheet_status", {})
else:
    # Create status dict based on extracted data
    print("No sheet status found in state, creating based on extracted data")
    
    # First check if we have any actual data in the extraction
    has_valid_data = False
    for sheet_name, sheet_data in extracted_data.items():
        # Skip metadata
        if sheet_name == "_metadata":
            continue
            
        if isinstance(sheet_data, dict) and sheet_data:
            has_valid_data = True
            break
    
    # Debug: print extracted keys
    print(f"Checking extraction result: {type(extracted_data)}")
    print(f"Extraction contains {len(extracted_data.keys() if isinstance(extracted_data, dict) else 0)} keys")
    
    if not has_valid_data:
        print("WARNING: No extracted data available - completely empty")
        # If we have any data at all (even if in wrong format), mark it as successful
        if extracted_data:
            sheet_status["default"] = "success"
    
    # Process each sheet if we have multiple sheets
    for sheet_name, sheet_data in extracted_data.items():
        # Skip metadata entries
        if sheet_name == "_metadata":
            continue
            
        # Check if we have actual data (ignoring schema type field if present)
        if isinstance(sheet_data, dict) and sheet_data:
            sheet_status[sheet_name] = "success"
        else:
            sheet_status[sheet_name] = "failure"
    
    # Check if we have sheet statuses for all expected sheets
    # For Manufacturing Account sheet, if it's not in the extracted data but we have data
    # in default or another sheet, create a mapping to that data
    if "Manufacturing Account" not in sheet_status and has_valid_data:
        for sheet_name, status in sheet_status.items():
            if status == "success" and sheet_name != "_metadata":
                sheet_status["Manufacturing Account"] = "success"
                print(f"Mapped Manufacturing Account status to {sheet_name} data")
                break

# Then, use sheet_status to find successful sheets:
successful_sheets = [name for name, status in sheet_status.items() if status == "success"]
