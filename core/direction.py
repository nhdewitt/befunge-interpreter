"""Direction enum for Befunge-93 instruction pointer movement.

Defines the movement directions, their (dx, dy) deltas, and display glyphs.
The coordinate system treats (0, 0) as the top-left corner: +x is east (right),
+x is west (left), +y is south (down), and −y is north (up). Movement wraps at
grid boundaries.

Notes:
  - Each direction has integer deltas `dx` and `dy` for movement.
  - `glyph` is the Befunge opcode character for the direction: '>', '<', '^', 'v'.
  - Random direction selection supports the '?' opcode.
"""

from enum import Enum
from random import choice

class Direction(Enum):
    """Movement direction for the instruction pointer.

    Members encode their movement deltas and display glyph.

    Members:
      RIGHT:  (dx=1,  dy=0, glyph='>')  Move east.
      LEFT:   (dx=-1, dy=0, glyph='<')  Move west.
      UP:     (dx=0,  dy=-1, glyph='^') Move north.
      DOWN:   (dx=0,  dy=1, glyph='v')  Move south.
    """
    RIGHT   = (1, 0, '>')
    LEFT    = (-1, 0, '<')
    UP      = (0, -1, '^')
    DOWN    = (0, 1, 'v')

    def __init__(self, dx: int, dy: int, glyph: str):
        """Bind movement deltas and the display glyph to the enum member."""
        self.dx = dx
        self.dy = dy
        self.glyph = glyph
    
    @staticmethod
    def random() -> "Direction":
        """Return a randomly selected cardinal direction.

        Used by the Befunge '?' opcode.

        Returns:
          One of RIGHT, LEFT, UP, or DOWN.
        """
        return choice([Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN])
    
    def __str__(self):
        """Return the direction name in lowercase."""
        return self.name.lower()