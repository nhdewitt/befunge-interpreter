"""
Defines the Direction enum for handling instruction pointer movement.

Coordinate System:
    - X: positive = east, negative = west
    - Y: positive = south, negative = north
    - Origin (0,0) is at top-left corner
    - Grid wraps around at boundaries

Direction Semantics:
    - Each direction has associated delta values (`dx`, `dy`) for movement
    - Glyph characters correspond to Befunge opcode
    - Random direction selection supports the `?` opcode
    - Conversion methods handle opcode character to direction mapping
"""

from enum import Enum
from random import choice

class Direction(Enum):
    """
    Enum of the IP movement directions.

    - `dx`, `dy`: Movement deltas
    - `glyph`: Befunge opcode character

    Attributes:
        `RIGHT` (opcode `>`): Move east (`dx=1`, `dy=0`)
        `LEFT` (opcode `<`): Move west (`dx=-1`, `dy=0`)
        `UP` (opcode `^`): Move north (`dx=0`, `dy=-1`)
        `DOWN` (opcode `v`): Move south (`dx=0`, `dy=1`)
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

    # @staticmethod
    # def from_opcode(ch: str) -> "Direction":
    #     """
    #     Convert a Befunge direction opcode character to a `Direction` enum.

    #     Maps the four opcodes to their corresponding `Direction` enum values:
    #     - `>`: Move right
    #     - `<`: Move left
    #     - `^`: Move up
    #     - `v`: Move down

    #     Args:
    #         `ch`: A single character representing a Befunge direction opcode
        
    #     Returns:
    #         The corresponding `Direction` enum value

    #     Example:
    #     ```
    #     >>> Direction.from_char('>')
    #     <Direction.RIGHT: (1, 0, '>')>
    #     >>> Direction.from_char('^')
    #     <Direction.UP: (0, -1, '^')>
    #     ```
    #     """
    #     return {
    #         '>':    Direction.RIGHT,
    #         '<':    Direction.LEFT,
    #         '^':    Direction.UP,
    #         'v':    Direction.DOWN,
    #     }[ch]
    
    @staticmethod
    def random() -> "Direction":
        """
        Return a random direction from the four cardinal directions.

        Used by the Befunge '?' opcode

        Returns:
            A randomly selection `Direction` from `RIGHT`, `LEFT`, `UP`, or `DOWN`
        """
        return choice([Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN])
    
    def __str__(self):
        """
        Return the direction name in lowercase.
        """
        return self.name.lower()