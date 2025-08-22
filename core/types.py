"""Shared types for the Befunge-93 interpreter.

Defines:
  - StepStatus: execution status after a step.
  - WaitTypes: the kind of input the interpreter is waiting for.
  - ViewState: a read-only snapshot of the interpreter state for GUIs.
"""

from dataclasses import dataclass
from enum import Enum, auto


class StepStatus(Enum):
    """Interpreter execution status.

    Used to communicate the current status after each execution step so
    the UI can react appropriately.
    """

    RUNNING = auto()            # executing normally
    AWAITING_INPUT = auto()     # waiting for user input
    HALTED = auto()             # terminated (reached '@')


class WaitTypes(Enum):
    """Type of user input the interpreter requires."""

    INT = "integer"
    CHAR = "character"


@dataclass
class ViewState:
    """Snapshot of interpreter state for GUI display.

    Provides the information needed to visualize the current state.

    Attributes:
      ip_x: Current IP x-coordinate.
      ip_y: Current IP y-coordinate.
      direction: Current movement direction as a glyph (e.g., '>', '<', '^', 'v').
      stack: Copy of current stack contents (bottom → top).
      output: Complete output produced so far.
      grid: Current program grid (list of rows, each a list of characters).
    """
    ip_x:       int
    ip_y:       int
    direction:  str
    stack:      list[int]
    output:     str
    grid:       list[list[str]]