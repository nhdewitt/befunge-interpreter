"""Befunge Instruction Pointer.

Implements the instruction pointer (IP) for a Befunge-93 interpreter.
The IP tracks its position and direction on a 2D playfield, supports
wraparound movement, and maintains execution state flags.

The playfield is at least 80×25 as per Befunge-93. Programs smaller
than this are padded on the right and bottom with spaces.
"""

from typing import Sequence, Optional, Tuple, Union, Final

from .direction import Direction
from .types import WaitTypes

MIN_WIDTH: Final[int]   = 80
"""Minimum playfield width (columns)."""

MIN_HEIGHT: Final[int]  = 25
"""Minimum playfield height (rows)."""

class InstructionPointer:
    """Manage the instruction pointer during program execution.

    Grid management:
      Programs are padded to the 80×25 minimum while preserving the
      original dimensions for bounds checks and visualization.

    Execution state:
      The IP tracks string mode, bridge/skip, random-direction metadata,
      and simple I/O wait state for GUI integration.

    Attributes:
      grid: 2D list of characters representing the program.
      width: Padded grid width (≥ 80).
      height: Padded grid height (≥ 25).
      orig_width: Original program width before padding.
      orig_height: Original program height before padding.
      x: Current column (0-based).
      y: Current row (0-based).
      direction: Current movement direction.
      skip: Whether the next move skips one cell (set by '#').
      string: Whether the IP is in string mode.
      last_was_random: True if the last direction change came from '?'.
      waiting_for: Expected input type, if any.
      pending_input: Buffered input value awaiting consumption.
    """
    def __init__(self, code: Union[str, Sequence[Sequence[str]]]) -> None:
        """Initialize the IP with Befunge source code.

        Converts input into a uniform 2D grid and pads to the standard
        80×25 playfield. Lines are right-padded with spaces; missing lines
        are appended as space-only rows.

        Args:
          code: Befunge source as a newline-separated string or a 2D
            sequence of characters.

        """
        if isinstance(code, str):
            lines = code.splitlines()
        else:
            lines = ["".join(row) for row in code]

        # Record original (pre-padding) dimensions for bounds/visualization.
        self.orig_width = max((len(l) for l in lines), default=0)
        self.orig_height = len(lines)

        # Pad to Befunge-93 minimums (80x25)
        W = max(MIN_WIDTH, self.orig_width)
        H = max(MIN_HEIGHT, self.orig_height)

        # Create uniform grid with right and bottom padding.
        self.grid: list[list[str]] = [list(l.ljust(W, ' ')) for l in lines]
        while len(self.grid) < H:
            self.grid.append([' '] * W)
        self.width, self.height = W, H

        self.x = 0
        self.y = 0
        self.direction: Direction = Direction.RIGHT

        # Execution state flags.
        self.skip = False                   # Bridge ('#') flag
        self.string = False                 # String mode flag
        self.last_was_random = False        # True if last direction change was '?'

        # I/O wait state for GUI integration.
        self.waiting_for: Optional[WaitTypes] = None    # Expected input type
        self.pending_input: Optional[int] = None        # Buffered input value
    
    def change_direction(self, d: Direction, *, from_random: bool = False) -> None:
        """Change the IP's movement direction.

        Args:
          d: New direction.
          from_random: True if the change came from the '?' opcode.

        """
        self.direction = d
        self.last_was_random = from_random
    
    def move(self) -> Tuple[int, int]:
        """Advance the IP one step with wraparound.

        Applies the current direction deltas. If `skip` is set (from '#'),
        an extra cell is skipped and the flag is cleared. Movement wraps
        around grid boundaries.

        Returns:
          The new `(x, y)` coordinates after movement.

        """
        dx, dy = self.direction.dx, self.direction.dy

        # If `skip` is set (from '#'), step once extra and clear it.
        if self.skip:
            self.x = (self.x + dx) % self.width
            self.y = (self.y + dy) % self.height
            self.skip = False

        self.x = (self.x + dx) % self.width
        self.y = (self.y + dy) % self.height

        return self.x, self.y