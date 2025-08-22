"""Arithmetic helpers matching Befunge-93 / C-like semantics."""

def trunc_div(a: int, b: int) -> int:
    """Truncating integer division (toward zero).

    Matches C semantics and Befunge-93 rules (division by zero yields 0).

    Args:
      a: Dividend (numerator).
      b: Divisor (denominator).

    Returns:
      The quotient truncated toward zero, or 0 if dividing by zero.

    Examples:
      >>> trunc_div(7, 3)
      2
      >>> trunc_div(-7, 3)
      -2
      >>> trunc_div(7, -3)
      -2
      >>> trunc_div(-7, -3)
      2
      >>> trunc_div(5, 0)
      0
    """
    if b == 0:
        return 0    # Befunge-93: division by zero -> 0
    # Do it purely with integers to avoid float rounding on huge values
    same_sign = (a >= 0) == (b >= 0)
    q = (abs(a) // abs(b))
    return q if same_sign else -q

def c_mod(a: int, b: int) -> int:
    """Modulo with C semantics (remainder has the same sign as the dividend).

    Befunge-93 specifies modulo-by-zero returns 0.

    Args:
      a: Dividend.
      b: Divisor.

    Returns:
      The remainder using truncating division (toward zero), or 0 if b == 0.

    Examples:
      >>> c_mod(7, 3)
      1
      >>> c_mod(-7, 3)
      -1
      >>> c_mod(7, -3)
      1
      >>> c_mod(-7, -3)
      -1
      >>> c_mod(5, 0)
      0
    """
    if b == 0:
        return 0    # Befunge-93: modulo by zero -> 0
    q = trunc_div(a, b)
    return a - q * b