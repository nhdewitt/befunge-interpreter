"""Befunge stack implementation.

Provides a stack with Befunge semantics: popping from an empty stack returns 0.
The stack stores integers and offers helpers commonly used by Befunge programs
(e.g., safe multi-pop, swap).
"""

from typing import Iterator, List, Tuple

class Stack:
    """Stack with Befunge-specific semantics.

    Popping from an empty stack returns 0 rather than raising an exception.
    The stack stores Python integers (the interpreter may impose 8/32-bit
    behavior elsewhere when reading/writing the grid).

    Attributes:
      items: Internal list storing stack elements (top is index -1).
    """
    def __init__(self) -> None:
        """Initialize an empty stack."""
        self.items: List[int] = []

    def __repr__(self) -> str:
        """Return a concise representation including size and contents.

        Examples:
          >>> s = Stack(); s.push(1); s.push(2); repr(s)
          'Size: 2 - Stack: [1, 2]'
        """
        return f"Size: {self.size()} - Stack: {self.items}"
    
    def __iter__(self) -> Iterator[int]:
        """Iterate from bottom to top.

        Examples:
          >>> s = Stack(); s.push(1); s.push(2); list(s)
          [1, 2]
        """
        return iter(self.items)
    
    def __len__(self) -> int:
        """Return the number of elements on the stack.

        Examples:
          >>> s = Stack(); len(s)
          0
          >>> s.push(1); len(s)
          1
        """
        return self.size()
    
    def __getitem__(self, idx: int) -> int:
        """Return the value at index (0 = bottom, -1 = top).

        Args:
          idx: Index to access.

        Returns:
          The value at the specified index.

        Raises:
          IndexError: If the index is out of range.

        Examples:
          >>> s = Stack(); s.push(10); s.push(20); s[0], s[-1]
          (10, 20)
        """
        return self.items[idx]
    
    def push(self, item: int) -> None:
        """Push a value onto the top of the stack.

        Args:
          item: Integer value to push.

        Examples:
          >>> s = Stack(); s.push(10); s.peek()
          10
        """
        self.items.append(item)

    def size(self) -> int:
        """Return the current number of elements on the stack.

        Examples:
          >>> s = Stack(); s.size()
          0
          >>> s.push(10); s.size()
          1
        """
        return len(self.items)
    
    def peek(self) -> int:
        """Return the top element without removing it (0 if empty).

        Examples:
          >>> s = Stack(); s.peek()
          0
          >>> s.push(10); s.peek()
          10
        """
        return self.items[-1] if self.items else 0
    
    def pop(self) -> int:
        """Remove and return the top element (0 if empty).

        Examples:
          >>> s = Stack(); s.pop()
          0
          >>> s.push(10); s.pop(), s.size()
          (10, 0)
        """
        return self.items.pop() if self.size() > 0 else 0
    
    def pop_two(self) -> Tuple[int, int]:
        """Pop two elements and return them as (top, next).

        Missing values are treated as 0.

        Returns:
          A tuple (top, second):
            - With ≥2 elements: (top, next).
            - With 1 element: (top, 0) and the stack becomes empty.
            - With 0 elements: (0, 0).

        Examples:
          >>> s = Stack(); s.push(10); s.push(20); s.pop_two()
          (20, 10)
          >>> s.push(10); s.pop_two()
          (10, 0)
          >>> s.pop_two()
          (0, 0)
        """
        match self.size():
            case 0:
                return 0, 0
            case 1:
                return self.pop(), 0
            case _:
                return self.pop(), self.pop()
    
    def stack_swap(self) -> None:
        """Swap the top two stack elements (missing values are 0).

        Behavior:
          - ≥2 elements: swap top two.
          - 1 element: result is [a, 0].
          - 0 elements: result is [0, 0].

        Examples:
          >>> s = Stack(); s.stack_swap(); s.items
          [0, 0]
          >>> s = Stack(); s.push(7); s.stack_swap(); s.items
          [7, 0]
          >>> s = Stack(); s.push(1); s.push(2); s.stack_swap(); s.items
          [2, 1]
        """
        b, a = self.pop_two()
        self.push(b)
        self.push(a)