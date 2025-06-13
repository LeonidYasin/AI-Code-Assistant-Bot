"""
Text formatting utilities.
"""
from typing import Optional, List, Union

def code_block(text: str, language: Optional[str] = None) -> str:
    """
    Format text as a Markdown code block.
    
    Args:
        text: The text to format.
        language: The language for syntax highlighting (e.g., 'python', 'javascript').
        
    Returns:
        The formatted text as a Markdown code block.
    """
    # Remove existing code block markers if present
    text = text.strip()
    if text.startswith('```') and text.endswith('```'):
        text = text[3:-3].strip()
        # Remove language specifier if present
        if '\n' in text:
            first_line, rest = text.split('\n', 1)
            if ' ' not in first_line.strip() and '\t' not in first_line.strip():
                text = rest
    
    # Add language specifier if provided
    if language:
        return f"```{language}\n{text}\n```"
    return f"```\n{text}\n```"

def indent(text: str, prefix: str = '  ') -> str:
    """
    Indent each line of text with the given prefix.
    
    Args:
        text: The text to indent.
        prefix: The prefix to add to each line.
        
    Returns:
        The indented text.
    """
    return '\n'.join(f"{prefix}{line}" if line.strip() else line 
                     for line in text.split('\n'))

def format_list(items: List[str], bullet: str = '-') -> str:
    """
    Format a list of strings as a bulleted list.
    
    Args:
        items: The list items to format.
        bullet: The bullet character to use.
        
    Returns:
        The formatted bulleted list as a string.
    """
    return '\n'.join(f"{bullet} {item}" for item in items if item.strip())

def truncate(text: str, max_length: int = 100, ellipsis: str = '...') -> str:
    """
    Truncate text to a maximum length, adding an ellipsis if truncated.
    
    Args:
        text: The text to truncate.
        max_length: Maximum length of the text.
        ellipsis: The ellipsis string to add if text is truncated.
        
    Returns:
        The truncated text with ellipsis if it was truncated.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(ellipsis)] + ellipsis
