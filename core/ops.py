"""Opcode dispatch table for the Befunge-93 interpreter.

Builds a mapping from opcode characters to zero-arg callables bound to a specific
`Interpreter` instance. Each callable performs the opcode’s effect and returns
either `None` (continue) or `StepStatus.AWAITING_INPUT` when input is needed.

Notes:
  - Digits, spaces, quotes, and '@' are handled directly in the interpreter loop.
  - Division uses `trunc_div` and modulo uses `c_mod` to match Befunge semantics.
"""

from typing import Callable, Dict, Optional
import operator as op

from .direction import Direction
from .utils import trunc_div, c_mod
from .types import StepStatus, WaitTypes

# Zero-arg operation bound to an Interpreter; may request input
Op = Callable[[], Optional[StepStatus]]


def build_ops(self) -> Dict[str, Op]:
    """Return the opcode dispatch table bound to this interpreter.

    The returned dictionary maps single-character opcodes to callables. Most
    callables return `None`. For `&` and `~`, the callable sets the interpreter
    into an input-waiting state and returns `StepStatus.AWAITING_INPUT`.

    Implementation notes:
      - '_' and '|' use helpers that return *callables* at table-build time
        (so we call `self._if_h()`/`self._if_v()` here to capture `self`).
      - '\\\\' is escaped in the dictionary key.
      - Direction opcodes set the IP direction immediately.

    Returns:
      Dict mapping opcode characters to bound operation callables.
    """
    return {
        # Arithmetic.
        '+': lambda: self._bin(op.add),
        '-': lambda: self._bin(op.sub),
        '*': lambda: self._bin(op.mul),
        '/': lambda: self._bin(trunc_div),
        '%': lambda: self._bin(c_mod),

        # Comparison / logic.
        '`': self._gt,
        '!': self._not,

        # Self-modifying.
        'p': self._put,
        'g': self._get,

        # Input.
        '&': lambda: self._await(WaitTypes.INT),
        '~': lambda: self._await(WaitTypes.CHAR),

        # Flow conditionals.
        '_': self._if_h(),
        '|': self._if_v(),

        # Stack operations.
        ':': self._dup,
        '\\': self._swap,
        '$': self._pop1,

        # Output.
        '.': self._out_int,
        ',': self._out_char,

        # Direction changes.
        '>': lambda: self._set_dir(Direction.RIGHT),
        '<': lambda: self._set_dir(Direction.LEFT),
        '^': lambda: self._set_dir(Direction.UP),
        'v': lambda: self._set_dir(Direction.DOWN),
        '?': self._rand_dir,

        # Control flow.
        '#': self._bridge,
    }