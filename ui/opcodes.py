OPCODES: dict[str, tuple[str, str, str]] = {
    #From Befunge-93 Documentation (https://catseye.tc/view/Befunge-93/doc/Befunge-93.markdown)
    '+': ("(add)",              "<value1> <value2>",    "<value1 + value2>"),
    '-': ("(subtract)",         "<value1> <value2>",    "<value1 - value2>"),
    '*': ("(multiply)",         "<value1> <value2>",    "<value1 * value2>"),
    '/': ("(divide)",           "<value1> <value2>",    "<value1 / value2>"),
    '%': ("(modulo)",           "<value1> <value2>",    "<value1 mod value2"),
    '!': ("(not)",              "<value>",              "<0 if value non-zero, 1 otherwise>"),
    '`': ("(greater)",          "<value1> <value2>",    "<1 if value1 > value2, 0 otherwise>"),
    '>': ("(right)",            "",                     "PC -> right"),
    '<': ("(left)",             "",                     "PC -> left"),
    '^': ("(up)",               "",                     "PC -> up"),
    'v': ("(down)",             "",                     "PC -> down"),
    '?': ("(random)",           "",                     "PC -> right? left? up? down? ???"),
    '_': ("(horizontal if)",    "<boolean value>",      "PC->left if <value>, else PC->right"),
    '|': ("(vertical if)",      "<boolean value>",      "PC->up if <value>, else PC->down"),
    '"': ("(stringmode)",       "",                     "Toggles 'stringmode'"),
    ':': ("(dup)",              "<value>",              "<value> <value>"),
    '\\': ("(swap)",            "<value1> <value2",     "<value2> <value1>"),
    '$': ("(pop)",              "<value>",              "pops <value> but does nothing"),
    '.': ("(output int)",       "<value>",              "outputs <value> as integer"),
    ',': ("(output char)",      "<value>",              "outputs <value> as ASCII"),
    '#': ("(bridge)",           "",                     "'jumps' PC one farther; skips over next command"),
    'g': ("(get)",              "<x> <y>",              "value at (x,y)"),
    'p': ("(put)",              "<value> <x> <y>",      "puts <value> at (x,y)"),
    '&': ("(input int)",        "",                     "<value user entered>"),
    '~': ("(input char)",       "",                     "<character user entered>"),
    '@': ("(end)",              "",                     "ends program")
}
for d in "0123456789":
    OPCODES[d] = (f"(push {d})", "", f"{d}")

HEADERS = ("COMMAND", "INITIAL STACK (bot->top)", "RESULT (STACK)")

def _first_col(cmd: str, meaning: str) -> str:
    """Merges hovered character with command from opcodes"""
    return f"{cmd} {meaning}".rstrip()

def compute_widths(rows: dict[str, tuple[str, str, str]],
                   headers: tuple[str, str, str] = HEADERS) -> tuple[int, int, int]:
    """Computes max width of each column (either the header or the text underneath) and returns as a tuple (n, n, n)"""
    w0 = max(len(headers[0]), *(len(_first_col(cmd, v[0])) for cmd, v in rows.items()))
    w1 = max(len(headers[1]), *(len(v[0]) for v in rows.values()))
    w2 = max(len(headers[2]), *(len(v[1]) for v in rows.values()))

    w0 = max(w0, 10)
    w1 = max(w1, 10)
    w2 = max(w2, 14)

    return (w0, w1, w2)

def _pad(s: str, w: int) -> str:
    """Add whitespace padding to s"""
    return s + " " * (w - len(s))

def format_tooltip_for_opcode(cmd: str,
                              rows: dict[str, tuple[str, str, str]] = OPCODES,
                              widths: tuple[int, int, int] | None = None,
                              headers: tuple[str, str, str] = HEADERS,
                              gap: str = " ") -> str:
    """Formats the widths of the columns for the hovered opcode"""
    if cmd in rows:
        op, stack, result = rows[cmd]
    elif cmd.isdigit():
        op, stack, result = (f"(push {cmd})", "", cmd)
    elif cmd == " ":
        op, stack, result = ("(noop)", "", "no effect")
    else:
        op, stack, result = ("", "", "")
    
    c0 = _first_col(cmd, op)
    cells = (c0, stack, result)

    if widths is None:
        widths = compute_widths(rows, headers)
    w0, w1, w2 = widths

    # Grow if cell is wider
    e0 = max(w0, len(headers[0]), len(op))
    e1 = max(w1, len(headers[1]), len(stack))
    e2 = max(w2, len(headers[2]), len(result))
    e_widths: tuple[int, int, int] = (e0, e1, e2)
    
    header = gap.join(_pad(h, w) for h, w in zip(headers, e_widths))
    underline = gap.join("-" * w for w in e_widths)
    row = gap.join(_pad(s, w) for s, w in zip(cells, e_widths))
    return f"{header}\n{underline}\n{row}"
    