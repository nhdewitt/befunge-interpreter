"""Stack visualization formatting utilities."""

def fmt_stack_item(v: int) -> str:
    """Format a stack value as a fixed-width numeric field plus optional ASCII.

    - For small integers (≤ 4 digits), show a right-aligned number.
      If 0 ≤ v ≤ 255 and the character is printable, also show its `repr`.
    - For longer values, return a shortened number with an ellipsis.

    Args:
      v: Integer stack value to format.

    Returns:
      A human-friendly, fixed-width string for listbox display.

    Examples:
      >>> fmt_stack_item(65)      # 'A'
      "  65 'A'"
      >>> fmt_stack_item(10)      # newline is not printable
      '  10'
      >>> fmt_stack_item(-7)
      '  -7'
      >>> fmt_stack_item(12345)
      '123…'
    """
    v_str = str(v)

    if len(v_str) <= 4:
        # Show ASCII for 0..255 if printable.
        if 0 <= v <= 255:
            ch = chr(v)
            if ch.isprintable():
                return f"{v:>4} {repr(ch)}"
        return f"{v:>4}"
    
    # Abbreviate larger magnitudes with an ellipsis.
    return v_str[:3] + "…"