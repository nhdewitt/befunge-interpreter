"""
Defines the Direction enum for handling instruction pointer movement.

Coordinate System:
    - X: positive = east, negative = west
    - Y: positive = south, negative = north
    - Origin (0,0) is at top-left corner.
"""

from enum import Enum
from random import choice

class Direction(Enum):
    """
    Enum of the IP movement directions.

    - `dx`, `dy`: Movement deltas
    - `glyph`: Befunge opcode character

    Attributes:
        `RIGHT` (opcode `>`): Move east
        `LEFT` (opcode `<`): Move west
        `UP` (opcode `^`): Move north
        `DOWN` (opcode `v`): Move south
    """
    RIGHT   = (1, 0, '>')
    LEFT    = (-1, 0, '<')
    UP      = (0, -1, '^')
    DOWN    = (0, 1, 'v')

    def __init__(self, dx: int, dy: int, glyph: str):
        """
        Initialize a Direction with movement deltas and corresponding glyph.

        Args:
            `dx`: Change in x-coordinate (-1 left, 1 right, 0 vertical)
            `dy`: Change in y-coordinate (-1 up, 1 down, 0 horizontal)
            `glyph`: Befunge opcode character (used for display): `>`, `<`, `^`, `v`
        """
        self.dx = dx
        self.dy = dy
        self.glyph = glyph

    @classmethod
    def from_char(cls, ch: str) -> "Direction":
        """
        Convert a Befunge direction opcode character to a `Direction` enum.

        Maps the four opcodes to their corresponding `Direction` enum values:
        - `>`: Move right
        - `<`: Move left
        - `^`: Move up
        - `v`: Move down

        Args:
            `ch`: A single character representing a Befunge direction opcode
        
        Returns:
            The corresponding `Direction` enum value

        Example:
        ```
        >>> Direction.from_char('>')
        <Direction.RIGHT: (1, 0, '>')>
        >>> Direction.from_char('^')
        <Direction.UP: (0, -1, '^')>
        ```
        """
        return {
            '>':    cls.RIGHT,
            '<':    cls.LEFT,
            '^':    cls.UP,
            'v':    cls.DOWN,
        }[ch]
    
    @classmethod
    def random(cls) -> "Direction":
        """
        Return a random direction from the four cardinal directions.

        Used by the Befunge '?' opcode

        Returns:
            A randomly selection `Directon` from `RIGHT`, `LEFT`, `UP`, or `DOWN`
        """
        return choice([cls.RIGHT, cls.LEFT, cls.UP, cls.DOWN])
    
    def __str__(self):
        """
        Return the direction name in lowercase.
        """
        return self.name.lower()