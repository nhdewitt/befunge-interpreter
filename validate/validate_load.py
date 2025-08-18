from pathlib import Path
from typing import Union

ALLOWED_EXTENSIONS = {".bf", ".befunge"}
BEFUNGE_HINT_CHARS = set('><^v@"&~_|\\$.,+-*/%`!pg0123456789')

def is_befunge_path(path: Union[str, Path]) -> bool:
    return Path(path).suffix.lower() in ALLOWED_EXTENSIONS

def possibly_valid_befunge(src: str, require_halt: bool = False) -> bool:
    if not src:
        return True
    if "\x00" in src:       # binary file check
        return False
    if require_halt and "@" not in src:
        return False
    return any(ch in BEFUNGE_HINT_CHARS for ch in src)