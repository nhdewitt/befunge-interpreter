import string

def fmt_stack_item(v: int) -> str:
    """Formats stack items to show int and char (if mappable)."""
    ch = chr(v % 256)
    if ch in string.printable and ch not in "\r\n\t\x0b\x0c":
        return f"{v:>4} {repr(ch)}"
    return f"{v:>4}"