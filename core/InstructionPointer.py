"""
Befunge Instruction Pointer

Implements the IP for a Befunge interpreter. The IP maintains the current
position and direction within the 2D grid, handles movement with wraparound,
and manages execution state.
"""

from typing import Sequence, Optional, Tuple, Union

from .direction import Direction
from .types import WaitTypes

MIN_WIDTH   = 80
MIN_HEIGHT  = 25

class InstructionPointer:
    """
    Manages the IP for program execution.

    Attributes
        `grid`: 2D list representing the Befunge program code
        `width`: Width of the program grid (min. 80 chars)
        `height`: Height of the program grid (min. 25 lines)
        `x`: Current x-coordinate (column) of the IP
        `y`: Current y-coordinate (row) of the IP
        `direction`: Current movement direction of the IP
        `skip`: Whether or not the next move should skip a cell
        `string`: Whether or not the IP is in string mode
        `steps`: Number of cycles run
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
        # standardize input
        if isinstance(code, str):
            lines = code.splitlines()
        else:
            lines = ["".join(row) for row in code]

        # Store original dimensions before padding
        self.orig_width = max((len(l) for l in lines), default=0)
        self.orig_height = len(lines)

        # calculate dimensions
        W = max(MIN_WIDTH, self.orig_width)
        H = max(MIN_HEIGHT, self.orig_height)

        # create uniform grid with padding
        self.grid: list[list[str]] = [list(l.ljust(W, ' ')) for l in lines]
        while len(self.grid) < H:
            self.grid.append([' '] * W)
        self.width, self.height = W, H

        # initialize IP state
        self.x = 0
        self.y = 0
        self.direction: Direction = Direction.RIGHT

        # execution state flags
        self.skip = False
        self.string = False
        self.last_was_random = False

        # I/O states
        self.waiting_for: Optional[WaitTypes] = None
        self.pending_input: Optional[int] = None
    
    def change_direction(self, d: Direction, *, from_random: bool = False) -> None:
        """
        Update the IP's direction based on a token or Direction

        Args:
            `d`: A `Direction` enum value

        Side Effects:
            - Sets `self.last_was_random` for random direction changes
            - May set `self.skip` flag for bridge commands 
        """
        self.direction = d
        self.last_was_random = from_random
    
    def move(self) -> Tuple[int, int]:
        """
        Move the IP one step in its current direction.

        Handles movement with wraparound. If the `skip` flag is set,
        moves an additional step to skip over the next cell.

        Returns:
            Tuple of `(x, y)` coordinates after movement

        Side Effects:
            - Updates `self.x` and `self.y` coordinates
            - Resets `self.skip` flag if set
            - Ensures coordinates remain within bounds
        """
        dx, dy = self.direction.dx, self.direction.dy
        # handle bridge command ('#')
        if self.skip:
            self.x = (self.x + dx) % self.width
            self.y = (self.y + dy) % self.height
            self.skip = False
        self.x = (self.x + dx) % self.width
        self.y = (self.y + dy) % self.height

        return self.x, self.y