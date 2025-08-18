from typing import Callable, Dict, Optional
import operator as op

from .direction import Direction
from .utils import trunc_div, c_mod
from .types import StepStatus, WaitTypes

def build_ops(self) -> Dict[str, Callable[[], Optional[StepStatus]]]:
    """
    Returns the opcode dispatch table, bound to a specific Interpreter instance.
    Each callable returns either None or a StepStatus.
    """
    return {
        # Arithmetic
        '+': lambda: self._bin(op.add),
        '-': lambda: self._bin(op.sub),
        '*': lambda: self._bin(op.mul),
        '/': lambda: self._bin(trunc_div),
        '%': lambda: self._bin(c_mod),

        # Comparison / logic
        '`': self._gt,
        '!': self._not,

        # Self-modifying
        'p': self._put,
        'g': self._get,

        # Input
        '&': lambda: self._await(WaitTypes.INT),
        '~': lambda: self._await(WaitTypes.CHAR),

        # Flow conditionals
        '_': self._if_h(),
        '|': self._if_v(),

        # Stack ops
        ':': self._dup,
        '\\': self._swap,
        '$': self._pop1,

        # Output
        '.': self._out_int,
        ',': self._out_char,

        # Directions
        '>': lambda: self._set_dir(Direction.RIGHT),
        '<': lambda: self._set_dir(Direction.LEFT),
        '^': lambda: self._set_dir(Direction.UP),
        'v': lambda: self._set_dir(Direction.DOWN),
        '?': self._rand_dir,

        # Control flow
        '#': self._bridge,
    }