"""
Utilities for robust JSON parsing from LLM outputs.
Provides functions to handle common issues with LLM-generated JSON.
"""
import json
import re
from typing import Dict, Any, Optional


def attempt_json_repair(text: str) -> str:
    """
    Attempt to repair common JSON issues in LLM outputs.
    
    Args:
        text: The raw text containing potential JSON
        
    Returns:
        Repaired JSON text (or original if no repairs needed/possible)
    """
    # Remove any text before the first opening brace
    match = re.search(r'(\{.*)', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    
    # Strip any text after the JSON object
    stack = []
    in_string = False
    escape_next = False
    
    # Find the closing brace that matches the first opening brace
    for i, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\' and in_string:
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                stack.append(i)
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:  # We've found the closing brace for the outer object
                        text = text[:i+1]
                        break
    
    # Try to fix unclosed brackets and braces
    open_braces = text.count('{')
    close_braces = text.count('}')
    if open_braces > close_braces:
        text += '}' * (open_braces - close_braces)
    
    # Fix unterminated strings by checking for strings that start but don't end
    def fix_unterminated_strings(s):
        result = ""
        in_str = False
        escape = False
        
        for c in s:
            if c == '\\' and in_str:
                escape = not escape
            elif c == '"' and not escape:
                in_str = not in_str
            else:
                escape = False
                
            result += c
            
        # Close any unclosed strings
        if in_str:
            result += '"'
            
        return result
            
    text = fix_unterminated_strings(text)
    
    # Fix trailing commas in objects and arrays
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    
    return text


def parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to parse JSON from LLM output with robust error handling.
    
    Args:
        text: The text containing potential JSON
        
    Returns:
        Parsed JSON as a dictionary, or None if parsing completely failed
    """
    # First try direct parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to repair common issues
        repaired = attempt_json_repair(text)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            # If all attempts fail, return None
            return None
