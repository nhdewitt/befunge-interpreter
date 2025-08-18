"""
Befunge Opcode Documentation and Tooltip Formatting

This module contains documentation for all Befunge-93 opcodes and provides formatting utilities
for creating consistent, aligned tooltip displays. The documentation follows the official Befunge-93
specification and includes stack effects and behavioral descriptions for each operation.

The tooltip formatting system ensures consistent column alignment and appearance across all opcode
help displays, supporting the predefined opcodes and dynamically generated content for digits.
"""

from typing import Dict, Tuple, Optional

# From Befunge-93 Documentation (https://catseye.tc/view/Befunge-93/doc/Befunge-93.markdown)
# Format: opcode -> (description, initial_stack, result_stack)
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

    # Output operations
    '.': ("(output int)",       "<value>",              "outputs <value> as integer"),
    ',': ("(output char)",      "<value>",              "outputs <value> as ASCII"),

    # Flow control and grid manipulation
    '#': ("(bridge)",           "",                     "'jumps' PC one farther; skips over next command"),
    'g': ("(get)",              "<x> <y>",              "value at (x,y)"),
    'p': ("(put)",              "<value> <x> <y>",      "puts <value> at (x,y)"),

    # Input operations
    '&': ("(input int)",        "",                     "<value user entered>"),
    '~': ("(input char)",       "",                     "<character user entered>"),

    # Program termination
    '@': ("(end)",              "",                     "ends program")
}

# Add documentation for digit opcodes
for d in "0123456789":
    OPCODES[d] = (f"(push {d})", "", f"{d}")

# Column headers
HEADERS = ("COMMAND", "INITIAL STACK (bot->top)", "RESULT (STACK)")

def _first_col(cmd: str, meaning: str) -> str:
    """
    Combine the command character with its description for the first column.

    Creates the first column content by merging the opcode character with its
    descriptive text, handling empty descriptions gracefully.

    Args:
        `cmd`: The opcode glyph
        `meaning`: The descriptive text

    Returns:
        Formatted string for the first column with trailing whitespace removed

    Example:
        ```
        >>> _first_col('+', '(add)')
        '+ (add)'
        >>> _first_col('5', '(push 5)')
        '5 (push 5)'
        ```
    """
    return f"{cmd} {meaning}".rstrip()

def compute_widths(rows: Dict[str, Tuple[str, str, str]],
                   headers: Tuple[str, str, str] = HEADERS) -> Tuple[int, int, int]:
    """
    Calculate optimal column widths for aligned tooltip display.

    Determines the max width needed for each column, which will either be the header
    of the column or the column data itself.

    Args:
        `rows`: Dict of opcode documentation
        `headers`: Column header strings for width calculation

    Returns:
        Tuple of `(width1, width2, width3)` for the three tooltip columns

    """
    w0 = max(len(headers[0]), *(len(_first_col(cmd, v[0])) for cmd, v in rows.items()))
    w1 = max(len(headers[1]), *(len(v[1]) for v in rows.values()))
    w2 = max(len(headers[2]), *(len(v[2]) for v in rows.values()))

    return (w0, w1, w2)

def _pad(s: str, w: int) -> str:
    """
    Add whitespace padding to achieve the specified width.

    Args:
        `s`: String to pad
        `w`: Target width

    Returns:
        String padded with spaces to reach the target width
    """
    return s + " " * (w - len(s))

def format_tooltip_for_opcode(cmd: str,
                              rows: Dict[str, Tuple[str, str, str]] = OPCODES,
                              widths: Optional[Tuple[int, int, int]] = None,
                              headers: Tuple[str, str, str] = HEADERS,
                              gap: str = " ") -> str:
    """
    Format a tooltip for a given Befunge opcode.

    Creates a formatted, aligned table showing the opcode's function, initial
    and resulting stack. Handles special cases for digits, spaces, and
    unknown characters gracefully.

    Args:
        `cmd`: The opcode character to format documentation for
        `rows`: Dict of opcode documentation
        `widths`: Pre-calculated column widths
        `headers`: Column header strings
        `gap`: String used to separate columns

    Returns:
        Multi-line string containing formatted tooltip with headers,
        separator line, and opcode information

    Example:
        ```
        >>> format_tooltip_for_opcode('+')
        'COMMAND          INITIAL STACK (bot->top)    RESULT (STACK)
         -------          ------------------------    -----------------
         + (add)          <value1> <value2>           <value1 + value2>'
        ```

    Special Handling:
        - Digits: Shows "`(push n)`" behavior with the digit value
        - Spaces: Shows `(noop)` with no effect
        - Unknown chars: Shows empty documentation
    """
    # Look up opcode documentation with fallbacks for special cases
    if cmd in rows:
        op, stack, result = rows[cmd]
    elif cmd.isdigit():
        # Digits push their numeric value
        op, stack, result = (f"(push {cmd})", "", cmd)
    elif cmd == " ":
        # Spaces are no-ops
        op, stack, result = ("(noop)", "", "no effect")
    else:
        # Unknown characters get empty documentation
        op, stack, result = ("", "", "")
    
    # Prepare content for formatting
    c0 = _first_col(cmd, op)
    cells = (c0, stack, result)

    # Calculate column widths
    if widths is None:
        widths = compute_widths(rows, headers)
    w0, w1, w2 = widths

    # Expand column widths if current content is wider than pre-calculated
    e0 = max(w0, len(headers[0]), len(op))
    e1 = max(w1, len(headers[1]), len(stack))
    e2 = max(w2, len(headers[2]), len(result))
    e_widths: Tuple[int, int, int] = (e0, e1, e2)
    
    # Format the three-line tooltip: header, separator, content
    header = gap.join(_pad(h, w) for h, w in zip(headers, e_widths))
    underline = gap.join("-" * w for w in e_widths)
    row = gap.join(_pad(s, w) for s, w in zip(cells, e_widths))

    return f"{header}\n{underline}\n{row}"