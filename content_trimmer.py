"""
Utilities for text content trimming to meet token limits
"""

def trim_content_for_model(content, max_tokens=1000, preserve_headers=True, important_tokens=None):
    """
    Trims content to fit within token limits while preserving important sections
    
    Args:
        content: The text content to trim
        max_tokens: Maximum number of tokens to keep (rough estimate)
        preserve_headers: Whether to prioritize headers/section titles
        important_tokens: List of important tokens to prioritize
        
    Returns:
        Trimmed content
    """
    # Simple tokenization - splitting by whitespace is a rough approximation
    tokens = content.split()
    
    if len(tokens) <= max_tokens:
        return content  # No trimming needed
    
    # Basic approach: Keep first quarter and last quarter, trim middle
    if max_tokens >= 200:
        # Keep first section (likely contains headers)
        first_section = int(max_tokens * 0.7)
        # Keep end section (may contain summaries)
        last_section = int(max_tokens * 0.3)
        
        first_part = ' '.join(tokens[:first_section])
        last_part = ' '.join(tokens[-last_section:])
        
        return f"{first_part}\n\n[...content trimmed to fit token limits...]\n\n{last_part}"
    else:
        # For very small token limits, just keep the beginning
        return ' '.join(tokens[:max_tokens]) + "..."
