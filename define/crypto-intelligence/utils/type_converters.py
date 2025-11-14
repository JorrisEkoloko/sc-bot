"""Type conversion utilities for safe data handling."""
from typing import Optional, Union, Any


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    if value is None:
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """
    Safely convert value to int.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Int value or default
    """
    if value is None:
        return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """
    Safely convert value to string.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        String value or default
    """
    if value is None:
        return default
    
    try:
        return str(value)
    except (ValueError, TypeError):
        return default


def safe_percentage(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Safely convert value to percentage float.
    
    Handles both decimal (0.05) and percentage (5) formats.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float percentage or default
    """
    if value is None:
        return default
    
    try:
        float_val = float(value)
        # If value is very small (< 1), assume it's decimal format (0.05 = 5%)
        # Otherwise assume it's already percentage format (5 = 5%)
        return float_val
    except (ValueError, TypeError):
        return default
