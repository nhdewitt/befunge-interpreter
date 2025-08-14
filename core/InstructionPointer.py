"""
Befunge Instruction Pointer

Implements the IP for a Befunge interpreter. The IP maintains the current
position and direction within the 2D grid, handles movement with wraparound
and manages execution state.
"""

from typing import Sequence, Tuple, Optional, Union
from random import choice
from core.direction import Direction

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
        `waiting_for`: Type of input expected (`int`, `char` or `None`)
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

        # calculate dimensions
        W = max((len(l) for l in lines), default=0)
        H = len(lines)
        W = max(80, W)
        H = max(25, H)

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
        self.steps = 1
        self.last_was_random = False

        # I/O states
        self.waiting_for: Optional[str] = None
        self.pending_input: Optional[int] = None

    def shuffle(self):
        """
        Generate a random direction for the '`?`' opcode.

        Returns:
            A randomly selected `Direction`
        """
        return Direction.random()
    
    def change_direction(self, token: Union[str, Direction]):
        """
        Update the IP's direction based on a token or Direction

        Handles various commands:
        - `Direction` objects: Set direction directly
        - `>`, `<`, `^`, `v`: Set cardinal direction
        - `?`: Set random direction
        - `#`: No direction change, but sets the skip flag

        Args:
            `token`: Either a `Direction` enum value or a string
                     representing a direction/control opcode

        Side Effects:
            - Updates `self.direction` for most tokens
            - Sets `self.last_was_random` for random direction changes
            - May set `self.skip` flag for bridge commands 
        """
        if isinstance(token, Direction):
            self.direction = token
            self.last_was_random = False
            return
        if token == '?':
            self.direction = Direction.random()
            self.last_was_random = True
            return
        if token == '#':
            return

        self.direction = Direction.from_char(token)
        self.last_was_random = False
    
    def move(self):
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