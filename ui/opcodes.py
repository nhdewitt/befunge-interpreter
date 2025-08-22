"""Befunge opcode documentation and tooltip formatting.

Contains documentation for all Befunge-93 opcodes and utilities to render
aligned, monospaced tooltip tables. The docs include stack effects and
behavioral descriptions derived from the Befunge-93 spec.

The formatter keeps column widths consistent across predefined opcodes and
dynamically generated entries (e.g., digits).
"""

from typing import Dict, Tuple, Optional

# Format: opcode -> (description, initial_stack, result_stack)
# Reference: https://catseye.tc/view/Befunge-93/doc/Befunge-93.markdown
OPCODES: Dict[str, Tuple[str, str, str]] = {
    # Artithmetic operations
    '+': ("(add)",              "<value1> <value2>",    "<value1 + value2>"),
    '-': ("(subtract)",         "<value1> <value2>",    "<value1 - value2>"),
    '*': ("(multiply)",         "<value1> <value2>",    "<value1 * value2>"),
    '/': ("(divide)",           "<value1> <value2>",    "<value1 / value2>"),
    '%': ("(modulo)",           "<value1> <value2>",    "<value1 mod value2"),

    # Comparison and logical operations
    '!': ("(not)",              "<value>",              "<0 if value non-zero, 1 otherwise>"),
    '`': ("(greater)",          "<value1> <value2>",    "<1 if value1 > value2, 0 otherwise>"),

    # Direction control opcodes
    '>': ("(right)",            "",                     "PC -> right"),
    '<': ("(left)",             "",                     "PC -> left"),
    '^': ("(up)",               "",                     "PC -> up"),
    'v': ("(down)",             "",                     "PC -> down"),
    '?': ("(random)",           "",                     "PC -> right? left? up? down? ???"),

    # Conditional flow control
    '_': ("(horizontal if)",    "<boolean value>",      "PC->left if <value>, else PC->right"),
    '|': ("(vertical if)",      "<boolean value>",      "PC->up if <value>, else PC->down"),

    # String mode and stack manipulation
    '"': ("(stringmode)",       "",                     "Toggles 'stringmode'"),
    ':': ("(dup)",              "<value>",              "<value> <value>"),
    '\\': ("(swap)",            "<value1> <value2>",    "<value2> <value1>"),
    '$': ("(pop)",              "<value>",              "pops <value> but does nothing"),

    # Output
    '.': ("(output int)",       "<value>",              "outputs <value> as integer"),
    ',': ("(output char)",      "<value>",              "outputs <value> as ASCII"),

    # Flow control and grid manipulation
    '#': ("(bridge)",           "",                     "'jumps' PC one farther; skips over next command"),
    'g': ("(get)",              "<x> <y>",              "value at (x,y)"),
    'p': ("(put)",              "<value> <x> <y>",      "puts <value> at (x,y)"),

    # Input
    '&': ("(input int)",        "",                     "<value user entered>"),
    '~': ("(input char)",       "",                     "<character user entered>"),

    # Program termination
    '@': ("(end)",              "",                     "ends program")
}

# Add documentation for digit opcodes
for d in "0123456789":
    OPCODES[d] = (f"(push {d})", "", f"{d}")

# Column headers
HEADERS: Tuple[str, str, str] = ("COMMAND", "INITIAL STACK (bot->top)", "RESULT (STACK)")

def _first_col(cmd: str, meaning: str) -> str:
    """Combine the opcode glyph with its short description.

    Args:
      cmd: The opcode character.
      meaning: The descriptive text (may be empty).

    Returns:
      The first-column content with trailing whitespace removed.

    Examples:
      >>> _first_col('+', '(add)')
      '+ (add)'
      >>> _first_col('5', '(push 5)')
      '5 (push 5)'
      >>> _first_col('>', '')
      '>'
    """
    return f"{cmd} {meaning}".rstrip()


def compute_widths(
        rows: Dict[str, Tuple[str, str, str]],
        headers: Tuple[str, str, str] = HEADERS
    ) -> Tuple[int, int, int]:
    """Calculate optimal column widths for aligned tooltip display.

    The width of each column is the max of the header and all row values.

    Args:
      rows: Dict of opcode docs.
      headers: Column headers used for width calculation.

    Returns:
      A tuple (w0, w1, w2) for the three tooltip columns.
    """
    w0 = max(len(headers[0]), *(len(_first_col(cmd, v[0])) for cmd, v in rows.items()))
    w1 = max(len(headers[1]), *(len(v[1]) for v in rows.values()))
    w2 = max(len(headers[2]), *(len(v[2]) for v in rows.values()))
    return (w0, w1, w2)


def _pad(s: str, w: int) -> str:
    """Pad a string with spaces to reach width w (no-op if already longer)."""
    return s if len(s) >= w else s + " " * (w - len(s))

def format_tooltip_for_opcode(
        cmd: str,
        rows: Dict[str, Tuple[str, str, str]] = OPCODES,
        widths: Optional[Tuple[int, int, int]] = None,
        headers: Tuple[str, str, str] = HEADERS,
        gap: str = " "
    ) -> str:
    """Format a tooltip table for a Befunge opcode.

    Produces a 3-column, monospaced table with headers, a separator, and a row
    describing the opcode’s meaning and stack effect.

    Args:
      cmd: Opcode character to format documentation for.
      rows: Opcode documentation mapping.
      widths: Optional precomputed column widths.
      headers: Column headers.
      gap: String used to separate columns.

    Returns:
      A multi-line string: header, underline, and content row.

    Examples:
      >>> print(format_tooltip_for_opcode('+').splitlines()[0])
      COMMAND INITIAL STACK (bot->top) RESULT (STACK)
    """
    # Look up opcode documentation with fallbacks for special cases.
    if cmd in rows:
        op, stack, result = rows[cmd]
    elif cmd.isdigit():
        op, stack, result = (f"(push {cmd})", "", cmd)
    elif cmd == " ":
        op, stack, result = ("(no-op)", "", "no effect")
    else:
        op, stack, result = ("", "", "")
    
    # Build first column and choose widths.
    c0 = _first_col(cmd, op)
    cells = (c0, stack, result)

    # Calculate column widths
    if widths is None:
        widths = compute_widths(rows, headers)

    # Expand widths if this row exceeds the precomputed sizes.
    w0, w1, w2 = widths
    e0 = max(w0, len(headers[0]), len(c0))
    e1 = max(w1, len(headers[1]), len(stack))
    e2 = max(w2, len(headers[2]), len(result))
    e_widths: Tuple[int, int, int] = (e0, e1, e2)
    
    # Render header, underline, and row.
    header = gap.join(_pad(h, w) for h, w in zip(headers, e_widths))
    underline = gap.join("-" * w for w in e_widths)
    row = gap.join(_pad(s, w) for s, w in zip(cells, e_widths))

    return f"{header}\n{underline}\n{row}"