def trunc_div(a: int, b: int) -> int:
    """
    Perform truncating integer division.

    Matches C-style truncation towards zero rather than Python's
    floor division.

    Args:
        `a`: Dividend (numerator)
        `b`: Divisor (denominator)
    
    Returns:
        The quotient truncated towards zero, or 0 if dividing by zero

    Example:
        ```
        >>> trunc_div(7, 3)
        2
        >>> trunc_div(-7, 3)
        -2
        >>> trunc_div(5, 0)
        0
        ```
    """
    if b == 0:
        return 0    # Befunge-93 defines as returning zero
    return int(a / b)

def c_mod(a: int, b: int) -> int:
    """
    Perform modulo operation with C-style semantics for negative numbers.

    Args:
        `a`: Dividend
        `b`: Divisor

    Returns:
        The remainder following C-style modulo rules, or 0 if modulo by zero

    Example:
        ```
        >>> c_mod(7, 3)
        1
        >>> c_mod(-7, 3)
        -1
        >>> c_mod(5, 0)
        0
        ```
    """
    if b == 0:
        return 0    # Befunge-93 defines as returning zero
    q = trunc_div(a, b)
    return a - q * b