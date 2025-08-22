"""Befunge-93 interpreter core.

Executes Befunge-93 programs on a 2D playfield. The interpreter drives the
instruction pointer (IP), manages the stack, handles I/O, and supports
step-by-step execution for debugging and visualization.

Features:
  - Full Befunge-93 opcode coverage.
  - String mode for literal text.
  - Self-modifying code via `p` (put) and `g` (get).
  - Asynchronous input handling for GUI integration.
  - Immutable view snapshots for debuggers/visualizers.
  - Extended 32-bit value storage for self-modifying code (shadow store).
"""

from __future__ import annotations

from io import StringIO
from typing import List, Callable, Dict, Union

from .InstructionPointer import InstructionPointer
from .direction import Direction
from .ops import build_ops
from .stack import Stack
from .types import StepStatus, ViewState, WaitTypes

class Interpreter:
    """Main Befunge-93 interpreter.

    Orchestrates program execution: maintains the execution stack, handles I/O,
    and exposes step-by-step execution suitable for GUI debuggers/visualizers.

    Extended storage:
      Values outside 0–255 are recorded in a shadow dictionary (`extended_storage`),
      while the visible grid holds the low byte for display. This allows full
      32-bit integers with `p`/`g` without losing visual fidelity.

    Attributes:
      stack: Execution stack.
      ip: Instruction pointer managing position and movement.
      output_stream: Buffer for program output (written by '.' and ',').
      halted: True once the program terminates with '@'.
      extended_storage: Map (x, y) → full int value for out-of-byte-range cells.
      _ops: Dispatch table mapping opcodes to implementation callables.
      grid_rev: Monotonic revision for tracking grid changes (e.g., GUI redraws).
    """
    def __init__(self, code: Union[str, List[List[str]]]):
        """Initialize the interpreter with Befunge source code.

        Builds the opcode dispatch table and loads the program.

        Args:
          code: Befunge source as a newline-separated string, or a 2D list
            of characters representing the program grid.
        """
        self._ops: Dict[str, Callable] = build_ops(self)
        self.load(code)

    @property
    def output(self) -> str:
        """Return all text written by '.' and ',' since the last load/reset."""
        return self.output_stream.getvalue()

    def load(self, code: Union[str, List[List[str]]]) -> None:
        """Load new source and reset interpreter state.

        Reinitializes the stack, IP, output buffer, and control flags. Increments
        the grid revision so UIs can detect content changes.

        Args:
          code: Befunge source as a string or a 2D character array.
        """
        self.stack: Stack = Stack()
        self.ip: InstructionPointer = InstructionPointer(code)
        self.output_stream = StringIO()
        self.halted = False

        # Track grid revision (load implies redraw).
        self.grid_rev = (getattr(self, "grid_rev", -1) + 1)

        # Shadow store for values outside 0–255 written via 'p'.
        # (x, y) → full int value; grid shows low byte for display.
        self.extended_storage: Dict[tuple[int, int], int] = {}

    def reset(self) -> None:
        """Reset the interpreter to initial state with the current program.

        Reloads from the current grid, resetting IP, stack, output, and control
        flags. Clears extended storage. Increments revision for GUI updates.
        """
        self.stack = Stack()
        self.ip = InstructionPointer(self.ip.grid)
        self.output_stream = StringIO()
        self.halted = False
        self.extended_storage.clear()
        self.grid_rev += 1
    
    def view(self) -> ViewState:
        """Return an immutable snapshot of the current interpreter state.

        Provides a GUI-safe view without exposing mutable internals.

        Returns:
          A ViewState containing the IP position/direction, stack, output, and grid.
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
        """Provide input when the interpreter is awaiting it.

        Used to satisfy `&` (integer input) or `~` (character input). The value is
        buffered and consumed on the next `step()`.

        Call this only after `step()` returned `AWAITING_INPUT`.

        Args:
          value: Input integer (for `~`, pass the ASCII code of the character).
        """
        self.ip.pending_input = value
        self.ip.waiting_for = None

    def step(self) -> StepStatus:
        """Execute one instruction (or input consumption) and advance the IP.

        Processing order:
          1. If an input value is pending, push it and move.
          2. Read the current cell.
          3. If not in string mode and cell is '@', halt.
          4. If cell is '"', toggle string mode.
          5. If in string mode, push ASCII value of the cell.
          6. Otherwise, execute opcode or push digit.
          7. Move the IP and report status.

        Returns:
          StepStatus.RUNNING while executing normally,
          StepStatus.AWAITING_INPUT if an opcode requested input,
          StepStatus.HALTED after '@'.
        """
        # Consume a pending input value (produced by GUI) and advance.
        if self.ip.pending_input is not None and self.ip.waiting_for is None:
            self.stack.push(self.ip.pending_input)
            self.ip.pending_input = None
            self.ip.move()
            return StepStatus.RUNNING
        
        # Read current character.
        ch = self.ip.grid[self.ip.y][self.ip.x]
        
        # Halt (only when not in string mode).
        if not self.ip.string and ch == '@':
            self.halted = True
            return StepStatus.HALTED
        
        # Toggle string mode.
        if ch == '"':
            self.ip.string = not self.ip.string
        # In string mode, push ASCII (quote toggles mode, not pushed).
        elif self.ip.string:
            self.stack.push(ord(ch))        
        # Space is a no-op.
        elif ch == ' ':
            pass
        # Digits push their integer value.
        elif ch.isdigit():
            self.stack.push(int(ch))
        else:
            # Dispatch opcode if known.
            opfn = self._ops.get(ch)
            if opfn:
                status = opfn()
                if status is StepStatus.AWAITING_INPUT:
                    return status
                
        # Advance to the next cell.
        self.ip.move()
        return StepStatus.RUNNING
    
    # ----- Opcode helpers -------------------------------------------------

    def _bin(self, fn: Callable[[int, int], int]) -> None:
        """Apply a binary function to the top two stack values.

        Pops b then a, applies fn(a, b), and pushes the result.

        Args:
          fn: Function taking two ints and returning an int.
        """
        a, b = self._pop_two_ab()
        self.stack.push(fn(a, b))

    def _gt(self) -> None:
        """Implement the '`' (greater-than) opcode.

        Pops b then a; pushes 1 if a > b, else 0.
        """
        a, b = self._pop_two_ab()
        self.stack.push(1 if a > b else 0)

    def _not(self) -> None:
        """Implement the '!' (logical NOT) opcode.

        Pops a value and pushes 1 if it was 0; otherwise pushes 0.
        """
        a = self._pop_or_zero()
        self.stack.push(0 if a else 1)

    def _put(self) -> None:
        """Implement the 'p' (put) opcode for self-modifying code.

        Pops y, x, v and writes to grid[y][x] (with wraparound).

        Extended storage:
          - 0–255: store chr(v) in the grid; clear any shadow value.
          - Outside 0–255: store full v in `extended_storage[(x, y)]`;
            grid shows low byte `abs(v) % 256` for visual reference.

        Stack effect: <v> <x> <y> → ()
        """
        y = self._pop_or_zero()
        x = self._pop_or_zero()
        v = self._pop_or_zero()

        h = len(self.ip.grid)
        w = len(self.ip.grid[0]) if self.ip.grid else 0

        if h and w:
            x = x % w
            y = y % h

            if v > 255 or v < 0:
                self.extended_storage[(x, y)] = v
                self.ip.grid[y][x] = chr(abs(v) % 256)
            else:
                self.ip.grid[y][x] = chr(v)
                if (x, y) in self.extended_storage:
                    del self.extended_storage[(x, y)]
        
        # Mark grid changed for GUI redraws.
        self.grid_rev += 1

    def _get(self) -> None:
        """Implement the 'g' (get) opcode for reading from the grid.

        Pops y, x and pushes the value at grid[y][x] (with wraparound).

        Extended storage:
          - If a shadow value exists at (x, y), push that full value.
          - Otherwise, push ord(grid char).
          - If the grid were empty, push 0.

        Stack effect: <x> <y> → <value>
        """
        y = self._pop_or_zero()
        x = self._pop_or_zero()

        h = len(self.ip.grid)
        w = len(self.ip.grid[0]) if self.ip.grid else 0

        if h and w:
            x = x % w
            y = y % h
            if (x, y) in self.extended_storage:
                self.stack.push(self.extended_storage[(x, y)])
            else:
                self.stack.push(ord(self.ip.grid[y][x]))
        
        else:
            self.stack.push(0)

    def _await(self, kind: WaitTypes) -> StepStatus:
        """Transition to an input-waiting state.

        Args:
          kind: WaitTypes.INT for '&' or WaitTypes.CHAR for '~'.

        Returns:
          StepStatus.AWAITING_INPUT to signal the UI to prompt for input.
        """
        self.ip.waiting_for = kind
        return StepStatus.AWAITING_INPUT

    def _if_h(self) -> Callable[[], None]:
        """Create handler for '_' (horizontal if).

        Returns:
          A callable that pops a value and sets RIGHT if it was 0, else LEFT.
        """
        return lambda: self.ip.change_direction(
            Direction.RIGHT if self._pop_or_zero() == 0 else Direction.LEFT
        )
    
    def _if_v(self) -> Callable[[], None]:
        """Create handler for '|' (vertical if).

        Returns:
          A callable that pops a value and sets DOWN if it was 0, else UP.
        """
        return lambda: self.ip.change_direction(
            Direction.DOWN if self._pop_or_zero() == 0 else Direction.UP
        )
    
    def _dup(self) -> None:
        """Implement the ':' (duplicate) opcode.

        Pushes a copy of the top value; if empty, pushes 0.

        Stack effect: <a> → <a> <a> ; () → <0>
        """
        self.stack.push(0 if self.stack.size() == 0 else self.stack.peek())

    def _swap(self) -> None:
        """Implement the '\\\\' (swap) opcode.

        Swaps the top two elements; missing values are treated as 0.

        Stack effect:
          <a> <b> → <b> <a>
          <a>     → <a> 0
          ()      → 0
        """
        match self.stack.size():
            case 0:
                self.stack.push(0)
            case 1:
                self.stack.push(0)
            case _:
                self.stack.stack_swap()

    def _pop1(self) -> None:
        """Implement the '$' (pop) opcode.

        Discards the top stack value. No effect on an empty stack.
        """
        if self.stack.size():
            self.stack.pop()
    
    def _out_int(self) -> None:
        """Implement the '.' (output integer) opcode.

        Pops a value and appends its decimal representation to the output.
        """
        self.output_stream.write(str(self._pop_or_zero()))

    def _out_char(self) -> None:
        """Implement the ',' (output character) opcode.

        Pops a value, converts `value % 256` to a character, and appends it.
        """
        self.output_stream.write(chr(self._pop_or_zero() % 256))

    def _set_dir(self, d: Direction) -> None:
        """Set the IP direction.

        Args:
          d: A Direction value.
        """
        self.ip.change_direction(d)

    def _rand_dir(self) -> None:
        """Implement the '?' (random direction) opcode.

        Sets the IP to a random cardinal direction.
        """
        self.ip.change_direction(Direction.random(), from_random=True)

    def _bridge(self) -> None:
        """Implement the '#' (bridge) opcode.

        Sets the skip flag so the next `move()` skips one cell.
        """
        self.ip.skip = True
    
    # ----- Stack helpers --------------------------------------------------

    def _pop_or_zero(self) -> int:
        """Pop and return the top value, or 0 if the stack is empty."""
        return self.stack.pop() if self.stack.size() > 0 else 0
    
    def _pop_two_ab(self) -> tuple[int, int]:
        """Pop two values with Befunge operand order.

        Returns:
          (a, b) where `a` is the left operand and `b` is the right.

        Example:
          If the stack is [5, 3], returns (5, 3) so that `a - b` is `5 - 3`.
        """
        b, a = self.stack.pop_two()
        return a, b