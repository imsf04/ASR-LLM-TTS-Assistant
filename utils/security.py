import os
from werkzeug.utils import secure_filename
from typing import Set

def validate_file(file, allowed_extensions: Set[str]) -> bool:
    """
    Validate uploaded file
    
    Args:
        file: Uploaded file object
        allowed_extensions: Set of allowed file extensions
    
    Returns:
        True if file is valid, False otherwise
    """
    if not file or not file.filename:
        return False
    
    # Check file extension
    filename = secure_filename(file.filename)
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    return secure_filename(filename)

def check_file_size(file, max_size: int) -> bool:
    """
    Check if file size is within limits
    
    Args:
        file: File object
        max_size: Maximum allowed size in bytes
    
    Returns:
        True if file size is acceptable
    """
    if hasattr(file, 'content_length') and file.content_length:
        return file.content_length <= max_size
    
    # For files without content_length, we'll check after saving
    return True

def validate_text_input(text: str, max_length: int = 10000) -> bool:
    """
    Validate text input
    
    Args:
        text: Input text
        max_length: Maximum allowed length
    
    Returns:
        True if text is valid
    """
    if not isinstance(text, str):
        return False
    
    if len(text.strip()) == 0:
        return False
    
    if len(text) > max_length:
        return False
    
    return True
