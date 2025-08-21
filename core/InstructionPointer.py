"""
Befunge Instruction Pointer

Implements the IP for a Befunge interpreter. The IP maintains the current
position and direction within the 2D grid, handles movement with wraparound,
and manages execution state.

Operates on a minimum 80x25 grid as per Befunge-93 specs, with automatic
padding for smaller programs and support for larger programs.
"""

from typing import Sequence, Optional, Tuple, Union

from .direction import Direction
from .types import WaitTypes

MIN_WIDTH   = 80
MIN_HEIGHT  = 25

class InstructionPointer:
    """
    Manages the IP for program execution.

    Grid Management:
        Programs are automatically padded to meet minimum Befunge-93 dimensions
        while preserving original program size information for bounds checking
        and visualization.

    Execution State:
        The IP maintains several execution flags including string mode, skip mode,
        and I/O state.

    Attributes
        `grid`: 2D list representing the Befunge program code
        `width`: Width of the program grid (min. 80 chars)
        `height`: Height of the program grid (min. 25 lines)
        `orig_width`: Original program width before padding
        `orid_height`: Original program height before padding
        `x`: Current x-coordinate (column) of the IP
        `y`: Current y-coordinate (row) of the IP
        `direction`: Current movement direction of the IP
        `skip`: Whether or not the next move should skip a cell
        `string`: Whether or not the IP is in string mode
        `last_was_random`: Whether the last direction change was random
        `waiting_for`: Type of input expected (`WaitTypes` or `None`)
        `pending_input`: Input value waiting to be processed
    """
    def __init__(self, code: Union[str, Sequence[Sequence[str]]]) -> None:
        """
        Initialize the IP with Befunge source code.

        Converts the input code to a standardized 2D grid format with
        minimum dimensions of 80x25 (standard Befunge-93 playfield size).
        Empty areas are filled with spaces, and lines are padded for
        uniform width.

        Args:
            `code`: Either a string containing Befunge source code with
                    newlines, or a 2D sequence of characters representing
                    the program grid
        """
        # Standardize input format
        if isinstance(code, str):
            lines = code.splitlines()
        else:
            lines = ["".join(row) for row in code]

        # Store original dimensions before padding for bounds checking
        self.orig_width = max((len(l) for l in lines), default=0)
        self.orig_height = len(lines)

        # Calculate padded dimensions to meet minimums
        W = max(MIN_WIDTH, self.orig_width)
        H = max(MIN_HEIGHT, self.orig_height)

        # Create uniform grid with right and bottom padding
        self.grid: list[list[str]] = [list(l.ljust(W, ' ')) for l in lines]
        while len(self.grid) < H:
            self.grid.append([' '] * W)
        self.width, self.height = W, H

        # Initialize IP at origin (0, 0) facing right
        self.x = 0
        self.y = 0
        self.direction: Direction = Direction.RIGHT

        # Execution state flags
        self.skip = False                   # Bridge command flag
        self.string = False                 # String mode flag
        self.last_was_random = False        # Random direction tracking

        # I/O synchronization state for GUI integration
        self.waiting_for: Optional[WaitTypes] = None    # Expected input type
        self.pending_input: Optional[int] = None        # Buffered input value
    
    def change_direction(self, d: Direction, *, from_random: bool = False) -> None:
        """
        Update the IP's direction based on a direction command.

        Args:
            `d`: A `Direction` enum value
            `from_random`: Whether this direction change came from a `?` opcode
        """
        self.direction = d
        self.last_was_random = from_random
    
    def move(self) -> Tuple[int, int]:
        """
        Move the IP one step in its current direction.

        Advances the IP position using the current direction's delta values, with
        wraparound at grid boundaries. If the `skip` flag is set (by `#`), moves an
        additional step to skip over the next cell, then clears the flag.

        Returns:
            Tuple of `(x, y)` coordinates after movement
        """
        dx, dy = self.direction.dx, self.direction.dy

        # Handle bridge command ('#')
        if self.skip:
            self.x = (self.x + dx) % self.width
            self.y = (self.y + dy) % self.height
            self.skip = False

        # Normal movement with wraparound
        self.x = (self.x + dx) % self.width
        self.y = (self.y + dy) % self.height

        return self.x, self.y