from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class StepStatus(Enum):
    """
    Enumeration of possible interpreter execution states.

    Used to communicate the current status of the interpreter after each
    execution state, allowing the GUI to respond appropriately.
    """
    RUNNING = auto()            # executing normally
    AWAITING_INPUT = auto()     # waiting for user input
    HALTED = auto()             # terminated (reached `@` opcode)

class WaitTypes(Enum):
    """
    Enumeration of possible user input types.

    Used to determine which type of input the interpreter requires from the user.
    """
    INT = "integer"
    CHAR = "character"

@dataclass
class ViewState:
    """
    Immutable snapshot of interpreter state for GUI display.

    Provides all necessary information for visualizing the current
    interpreter state without exposing mutable internal objects.

    Attributes:
        `ip_x`: Current IP x-coordinate
        `ip_y`: Current IP y-coordinate
        `direction`: Current movement direction as a string
        `stack`: Copy of current stack contents (bottom->top)
        `output`: Complete output string produced so far
        `grid`: Copy of the current program grid
    """
    ip_x:       int
    ip_y:       int
    direction:  str
    stack:      List[int]
    output:     str
    grid:       List[List[str]]