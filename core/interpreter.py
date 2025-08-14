"""
Befunge-93 Interpreter Core

Implements the main interpreter for the Befunge-93 programming language. Befunge is a
stack-based, 2D grid programming language where the IP moves through a grid of
characters, executing operations and manipulating a stack.

Handles all operations including arithmetic, stack manipulation, flow control,
I/O operations, and self-modifying code capabilities.

Key features:
    - Complete Befunge-93 opcode support (https://catseye.tc/view/Befunge-93/doc/Befunge-93.markdown)
    - String mode for literal character input
    - Self-modifying code (get/put ops)
    - Asynchronous input handling for GUI integration
    - Step-by-step execution for debugging and visualization
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Callable, Dict, Optional, Union
from random import choice
import operator as op

from core.InstructionPointer import InstructionPointer
from core.direction import Direction
from core.stack import Stack

def trunc_div(a: int, b: int) -> int:
    """
    Perform truncating integer division.

    Matches C-style truncation towards zero rather than Python's
    floor division.

    Args:
        `a`: Dividend (numerator)
        `b`: Divisor (denominator)
    
    Returns:
        The quotient truncated towards zero, or 0 if dividing by zero

    Example:
        ```
        >>> trunc_div(7, 3)
        2
        >>> trunc_div(-7, 3)
        -2
        >>> trunc_div(5, 0)
        0
        ```
    """
    if b == 0:
        return 0    # Befunge-93 defines as returning zero
    return int(a / b)

def c_mod(a: int, b: int) -> int:
    """
    Perform modulo operation with C-style semantics for negative numbers.

    Args:
        `a`: Dividend
        `b`: Divisor

    Returns:
        The remainder following C-style modulo rules, or 0 if modulo by zero

    Example:
        ```
        >>> c_mod(7, 3)
        1
        >>> c_mod(-7, 3)
        -1
        >>> c_mode(5, 0)
        0
        ```
    """
    if b == 0:
        return 0    # Befunge-93 defines as returning zero
    q = trunc_div(a, b)
    return a - q * b

class StepStatus(Enum):
    """
    Enumeration of possible interpreter execution states.

    Used to communicate the current status of the interpreter after each
    execution state, allowing the GUI to respond appropriately.
    """
    RUNNING = auto()            # executing normally
    AWAITING_INPUT = auto()     # waiting for user input
    HALTED = auto()             # terminated (reached `@` opcode)

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

class Interpreter:
    """
    Main Befunge-93 interpreter implementing complete language semantics.

    Manages program execution, maintains the execution stack, handles I/O
    operations, and provides step-by-step execution capabilities suitable
    for integration with GUI debuggers and visualizers.

    The interpreter supports:
    - All Befunge-93 opcodes
    - String mode for literal text input
    - Self-modifying code via `p` (put) and `g` (get) operations
    - Asynchronous input handling for GUI integration
    - Program state inspection and reset capabilities

    Attributes:
        `stack`: The execution stack for intermediate values
        `ip`: The IP managing position and movement
        `output`: Accumulated output from `.` and `,` operations
        `halted`: Whether the program has terminated
        `_ops`: Dictionary mapping opcodes to their implementation functions
    """
    def __init__(self, code: Union[str, List[List[str]]]):
        """
        Initialize the interpreter with Befunge source code.

        Args:
            `code`: Either a string containing Befunge source (with newlines),
                    or a 2D list of characters representing the program grid
        """
        # Initialize opcode dispatch table
        self._ops: Dict[str, Callable] = {
            # Arithmetic operations
            '+': lambda: self._bin(op.add),     # Addition
            '-': lambda: self._bin(op.sub),     # Subtraction
            '*': lambda: self._bin(op.mul),     # Multiplication
            '/': lambda: self._bin(trunc_div),  # Division (C-style)
            '%': lambda: self._bin(c_mod),      # Modulo (C-style)

            # Comparison and logic
            '`': self._gt,                      # Greater than
            '!': self._not,                     # Logical NOT

            # Self-modifying code
            'p': self._put,                     # Put character into grid
            'g': self._get,                     # Get character from grid

            # Input operations
            '&': lambda: self._await('int'),    # Read integer from user
            '~': lambda: self._await('char'),   # Read char from user

            # Flow control
            '_': self._if_h(),                  # Horizontal conditional
            '|': self._if_v(),                  # Vertical conditional

            # Stack operations
            ':': self._dup,                     # Duplicate top of stack
            '\\': self._swap,                   # Swap top two elements of stack
            '$': self._pop1,                    # Pop and discard

            # Output operations
            '.': self._out_int,                 # Output integer
            ',': self._out_char,                # Output character

            # Direction changes
            '>': lambda: self._set_dir(Direction.RIGHT),
            '<': lambda: self._set_dir(Direction.LEFT),
            '^': lambda: self._set_dir(Direction.UP),
            'v': lambda: self._set_dir(Direction.DOWN),
            '?': self._rand_dir,                # Random direction

            # Control flow
            '#': self._bridge,                  # Bridge (skip next cell)
        }

        self.load(code)

    def load(self, code: Union[str, List[List[str]]]) -> None:
        """
        Load new Befunge source code and reset interpreter state.

        Initializes all interpreter components with the provided code,
        resetting execution state to the beginning of the program.

        Args:
            `code`: Befunge source code as string or 2D character array
        """
        self.stack: Stack = Stack()
        self.ip: InstructionPointer = InstructionPointer(code)
        self.output = ""
        self.halted = False

    def reset(self) -> None:
        """
        Reset the interpreter to initial state with the same program.

        Reloads the current program grid, resetting the instruction pointer,
        stack, output, and all execution state while preserving any
        modifications made to the grid by `p` operations.
        """
        self.load(self.ip.grid)
    
    def view(self) -> ViewState:
        """
        Create an immutable snapshot of the current interpreter state.

        Provides a safe view of interpreter internals for GUI display without
        exposing mutable objects that could affect execution.

        Returns:
            `ViewState` containing current position, stack, output, and grid
        """
        return ViewState(
            ip_x=self.ip.x,
            ip_y=self.ip.y,
            direction=self.ip.direction.glyph,
            stack = list(self.stack),
            output = self.output,
            grid=self.ip.grid
        )
    
    def provide_input(self, value: int) -> None:
        """
        Provide input value to the interpreter when it's awaiting input.

        Used by the GUI to supply values for the `&` (integer input) and
        `~` (character input) operations. The value is buffered until the
        next `step()` call processes it.

        Args:
            `value`: Integer value to provide (for `~`, should be ASCII)
        """
        self.ip.pending_input = value
        self.ip.waiting_for = None

    def step(self) -> StepStatus:
        """
        Execute one step of the Befunge program.

        Processes the character at the current IP position, executes the
        corresponding operation, and advances the IP. Handles special
        cases like string mode, input waiting, and program termination.

        Returns:
            StepStatus indicating current interpreter state:
            - `RUNNING`: Normal execution, ready for next step
            - `AWAITING_INPUT`: Waiting for input via `provide_input()`
            - `HALTED`: Program terminated with `@` opcode

        Note:
            In string mode, most characters are pushed onto the stack as
            ASCII values rather than executed as opcodes.
        """
        # Process pending input from previous step
        if self.ip.pending_input is not None and self.ip.waiting_for is None:
            self.stack.push(self.ip.pending_input)
            self.ip.pending_input = None
            self.ip.move()
            return StepStatus.RUNNING
        
        # Get current character from grid
        ch = self.ip.grid[self.ip.y][self.ip.x]
        
        # Handle program termination
        if ch == '@':
            self.halted = True
            return StepStatus.HALTED
        
        # Handle string mode toggle
        if ch == '"':
            self.ip.string = not self.ip.string
        # While in string mode, push ASCII values (except for quotes)
        elif self.ip.string:
            self.stack.push(ord(ch))
        
        # Handle normal opcode execution
        elif ch == ' ':
            # Space is a noop
            pass

        # Digits 0-9 push their numeric value
        elif ch.isdigit():
            self.stack.push(ord(ch) - 48)

        else:
            # Look up and execute opcode
            opfn = self._ops.get(ch)
            if opfn:
                status = opfn()
                # Check if op requires input
                if status is StepStatus.AWAITING_INPUT:
                    return status
                
        # Move IP and continue
        self.ip.move()
        return StepStatus.RUNNING
    
    # Binary operation helper
    def _bin(self, fn: Callable[[int, int], int]) -> None:
        """
        Execute a binary operation on the top two stack elements.

        Pops two values from the stack, applies the given function,
        and pushes the result. Follows Befunge stack semantics where
        the second-popped value is the left operand.

        Args:
            `fn`: Function to apply (takes two ints, returns int)
        """
        a, b = self._pop_two_ab()
        self.stack.push(fn(a, b))

    def _gt(self) -> None:
        """
        Implement the  `` ` `` (greater than) opcode.

        Pops `b`, then `a`, and pushes 1 if `a > b`, otherwise 0
        """
        a, b = self._pop_two_ab()
        self.stack.push(1 if a > b else 0)

    def _not(self) -> None:
        """
        Implement the `!` (logical NOT) opcode.

        Pops a value and pushes 1 if it was 0, otherwise pushes 0.
        """
        a = self._pop_or_zero()
        self.stack.push(0 if a else 1)

    def _await(self, kind: str) -> StepStatus:
        """
        Set up the interpreter to wait for input of the specified type.

        Args:
            `kind`: Either `int` for `&` opcode or `char` for `~` opcode

        Returns:
            `StepStatus.AWAITING_INPUT` to signal GUI to request input
        """
        self.ip.waiting_for = kind
        return StepStatus.AWAITING_INPUT
    
    def _put(self) -> None:
        """
        Implement the `p` (put) opcode for self-modifying code.

        Pops `y`, `x`, and `v` from stack, then sets `grid[y][x] = chr(v)`.
        Coorinates wrap around grid boundaries. This allows Befunge
        programs to modify their own source code during execution.
        """
        y = self._pop_or_zero()
        x = self._pop_or_zero()
        v = self._pop_or_zero()
        h = len(self.ip.grid)
        w = len(self.ip.grid[0]) if self.ip.grid else 0
        if h and w:
            # Wrap coordinates and convert value to character
            self.ip.grid[y % h][x % w] = chr(v % 256)

    def _get(self) -> None:
        """
        Implement the `g` (get) opcode for reading from the grid.

        Pops `y` and `x` coordinates from stack, then pushes the
        ASCII value of the character at `grid[y][x]`. Coordinates
        wrap around grid boundaries.
        """
        y = self._pop_or_zero()
        x = self._pop_or_zero()
        h = len(self.ip.grid)
        w = len(self.ip.grid[0]) if self.ip.grid else 0
        if h and w:
            # Wrap coordinates and get ASCII value
            self.stack.push(ord(self.ip.grid[y % h][x % w]))
        else:
            self.stack.push(0)

    def _if_h(self) -> Callable:
        """
        Create handler for `_` (horizontal if) opcode.

        Returns a lambda that pops a value and sets direction to
        `RIGHT` if the value is 0, `LEFT` otherwise.

        Returns:
            Function that implements horizontal conditional logic.
        """
        return lambda: setattr(self.ip, "direction",
                               Direction.RIGHT if self._pop_or_zero() == 0 else Direction.LEFT)
    
    def _if_v(self) -> Callable:
        """
        Create handler for `|` (vertical if) opcode.

        Returns a lambda that pops a value and sets direction to
        `DOWN` if the value is 0, `UP` otherwise.

        Returns:
            Function that implements vertical conditional logic.
        """
        return lambda: setattr(self.ip, "direction",
                               Direction.DOWN if self._pop_or_zero() == 0 else Direction.UP)
    
    def _rand_dir(self) -> Direction:
        """
        Implement the `?` (random direction) opcode.

        Sets the instruction pointer direction to a random cardinal direction.
        """
        return Direction.random()
    
    def _dup(self) -> None:
        """
        Implement the `:` (duplicate) opcode.

        Pushes a copy of the top stack element. If the stack is empty, pushes 0
        following Befunge semantics.
        """
        self.stack.push(0 if self.stack.size() == 0 else self.stack.peek())

    def _swap(self) -> None:
        """
        Implement the `\\` (swap) opcode.

        Swaps the top two elements of the stack. Handles cases where the stack has
        fewer than two elements by treating missing values as 0.
        """
        n = self.stack.size()
        if n >= 2:
            self.stack.stack_swap()
        elif n == 1:
            # One element: swap with implicit 0
            a = self.stack.pop()
            self.stack.push(0)
            self.stack.push(a)
        else:
            # Empty stack: push 0 (swapping two implicit 0s)
            self.stack.push(0)

    def _pop1(self) -> None:
        """
        Implement the `$` (pop) opcode.

        Pops and discards the top element of the stack.
        Safe to call on empty stack (no effect).
        """
        if self.stack.size():
            self.stack.pop()
    
    def _out_int(self) -> None:
        """
        Implement the `.` (output integer) opcode.

        Pops a value from the stack and appends it to the output
        string as a decimal integer.
        """
        self.output += str(self._pop_or_zero())

    def _out_char(self) -> None:
        """
        Implement the `,` (output character) opcode.

        Pops a value from the stack, converts it to a character
        (modulo 256 for ASCII range), and appends to output.
        """
        self.output += chr(self._pop_or_zero() % 256)

    def _set_dir(self, d: Union[Direction, str]) -> None:
        """
        Set the IP direction.

        Args:
            `d`: Either a `Direction` enum value or a direction character
        """
        if isinstance(d, str):
            d = Direction.from_char(d)
        self.ip.direction = d

    def _bridge(self) -> None:
        """
        Implement the `#` (bridge) opcode.

        Sets the skip flag so the next `move()` call will skip over the
        next cell in the current direction.
        """
        self.ip.skip = True
    
    # Helper methods for common stack operations
    def _pop_or_zero(self) -> int:
        """
        Pop a value from the stack, returning 0 if stack is empty.

        Returns:
            Top stack value, or 0 if stack is empty
        """
        return self.stack.pop() if self.stack.size() > 0 else 0
    
    def _pop_two_ab(self) -> tuple[int, int]:
        """
        Pop two values with proper operand order for binary operations.

        In Befunge, the second value popped becomes the left operand and
        the first popped becomes the right.

        Returns:
            Tuple `(a, b)` where `a` is the left operand and `b` is the right

        Example:
            If stack is `[5, 3]`, `_pop_two_ab()` returns `(5, 3)` so that
            `5 - 3 = 2`, not `3 - 5 = -2`
        """
        b, a = self.stack.pop_two()
        return a, b