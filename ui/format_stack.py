"""
Stack Visualization Formatting Utility

Provides formatting function for displaying Befunge stack contents. The
formatting shows both numeric values and their ASCII character (when
applicable).
"""

import string

def fmt_stack_item(v: int) -> str:
    """
    Format a stack value for display, showing both numeric and character representations.

    Keeps fixed width with ellipsis for larger numbers.

    Args:
        `v`: Integer stack value to format
    """
    v_str = str(v)

    if len(v_str) <= 4:
        # Only try to show ASCII for valid positive integers
        if 0 <= v <= 255:
            ch = chr(v)
            # Check if character is suitable for display
            if ch in string.printable and ch not in "\r\n\t\x0b\x0c":
                return f"{v:>4} {repr(ch)}"
        return f"{v:>4}"
    
    return v_str[:3] + "…"