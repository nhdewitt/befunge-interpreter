"""Lightweight Befunge file/source heuristics.

- `is_befunge_path` checks filename extensions.
- `possibly_valid_befunge` does a quick content sniff (no NULs, has known
  opcode glyphs, optional requirement that a program contains '@').

These are intentionally permissive to avoid false negatives in editors/GUI.
"""

from pathlib import Path
from typing import Union

# Recognized filename extensions for Befunge-93 programs.
ALLOWED_EXTENSIONS = {".bf", ".befunge"}

# Heuristic set of glyphs that strongly suggest Befunge-93 source.
BEFUNGE_HINT_CHARS = frozenset(
    '><^v@"&~_|\\$.,+-*/%`!pg0123456789:#?'
)


def is_befunge_path(path: Union[str, Path]) -> bool:
    """Return True if the path has a known Befunge extension.

    Args:
      path: Filesystem path or string.

    Examples:
      >>> is_befunge_path("prog.bf")
      True
      >>> is_befunge_path("prog.befunge")
      True
      >>> is_befunge_path("prog.txt")
      False
    """
    return Path(path).suffix.lower() in ALLOWED_EXTENSIONS


def possibly_valid_befunge(src: str, require_halt: bool = False) -> bool:
    """Quick check that a string *could* be Befunge-93 source.

    Heuristics:
      - Empty strings are allowed (useful for new/unsaved buffers).
      - Reject if a NUL byte is present (likely a binary file).
      - If `require_halt` is True, require an '@' opcode to appear.
      - Otherwise, accept if *any* character appears from `BEFUNGE_HINT_CHARS`.

    Args:
      src: Source text to inspect.
      require_halt: If True, require an '@' opcode to be present.

    Returns:
      True if the text is *possibly* Befunge (heuristic), else False.

    Examples:
      >>> possibly_valid_befunge("")  # empty buffer allowed
      True
      >>> possibly_valid_befunge("12+,.@")
      True
      >>> possibly_valid_befunge("hello world")  # no hint glyphs
      False
      >>> possibly_valid_befunge("12+,.", require_halt=True)  # missing '@'
      False
      >>> possibly_valid_befunge("12+,.@\\x00")  # NUL -> reject
      False
    """
    if not src:
        return True # allow empty buffers
    if "\x00" in src:   # binary file check
        return False
    if require_halt and "@" not in src:
        return False
    return any(ch in BEFUNGE_HINT_CHARS for ch in src)