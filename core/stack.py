"""
Befunge Stack Implementation

Implements the stack data structure used by the interpreter. The
stack follows Befunge semantics where popping from an empty stack
returns 0, and provides specialized operations used in Befunge
programs.
"""

from typing import Iterator, Tuple

class Stack:
    """
    A stack implementation with Befunge-specific semantics.

    Follows Befunge conventions where attempting to pop from
    an empty stack returns 0 rather than raising an Exception.

    Stores integer values and supports all standard stack
    operations plus specialized methods for common Befunge
    patterns such as swapping the top two elements and popping
    multiple elements safely.

    Attributes:
        `items`: Internal list storing stack elements (top is idx -1)
    """
    def __init__(self):
        """
        Initialize an empty stack.

        Creates a new stack with no elements. All pop operations on an
        empty stack will return 0.
        """
        self.items: list[int] = []

    def __repr__(self):
        """
        Return a string representation showing stack size and contents.

        Returns:
            Formatted string with stack size and complete contents

        Example:
            ```
            >>> stack = Stack()
            >>> stack.push(1)
            >>> stack.push(2)
            >>> repr(stack)
            Size: 2 - Stack: [1, 2]
            ```
        """
        return f"Size: {self.size()} - Stack: {self.items}"
    
    def __iter__(self) -> Iterator[int]:
        """
        Return an iterator over stack contents from bottom to top.

        Returns:
            Iterator yielding stack elements in bottom-to-top order

        Example:
            ```
            >>> stack = Stack()
            >>> stack.push(1)
            >>> stack.push(2)
            >>> list(stack)
            [1, 2]
            ```
        """
        return iter(self.items)
    
    def __len__(self):
        """
        Return the number of elements on the stack.

        Returns:
            Number of elements currently on the stack

        Example:
            ```
            >>> stack = Stack()
            >>> len(stack)
            0
            >>> stack.push(1)
            >>> len(stack)
            1
            ```
        """
        return self.size()
    
    def __getitem__(self, idx: int) -> int:
        """
        Access stack elements by index (0 = bottom, -1 = top).

        Args:
            `idx`: Index to access

        Returns:
            The value at the specified index

        Example:
            ```
            >>> stack = Stack()
            >>> stack.push(10)
            >>> stack.push(20)
            >>> stack[0]
            10
            >>> stack[-1]
            20
            ```
        """
        return self.items[idx]
    
    def push(self, item: int):
        """
        Push a value onto the top of the stack.

        Args:
            `item`: Integer value to push onto the stack

        Example:
            ```
            >>> stack = Stack()
            >>> stack.push(10)
            >>> stack.peek()
            10
            ```
        """
        self.items.append(item)

    def size(self) -> int:
        """
        Return the current number of elements on the stack.

        Returns:
            Number of elements currently on the stack

        Example:
            ```
            >>> stack = Stack()
            >>> stack.size()
            0
            >>> stack.push(10)
            >>> stack.size()
            1
            ```
        """
        return len(self.items)
    
    def peek(self):
        """
        Return the top element without removing it from the stack.

        Returns 0 if the stack is empty.

        Returns:
            The top element if the stack is not empty, otherwise 0

        Example:
            ```
            >>> stack = Stack()
            >>> stack.peek()
            0
            >>> stack.push(10)
            >>> stack.peek()
            10
            ```
        """
        return self.items[-1] if self.items else 0
    
    def pop(self) -> int:
        """
        Remove and return the top element from the stack.

        Returns 0 if the stack is empty.

        Returns:
            The top element if the stack is not empty, otherwise 0

        Example:
            ```
            >>> stack = Stack()
            >>> stack.pop()
            0
            >>> stack.push(10)
            >>> stack.pop()
            10
            >>> stack.size()
            0
            ```
        """
        return self.items.pop() if self.size() > 0 else 0
    
    def pop_two(self) -> Tuple[int, int]:
        """
        Pop two elements from the stack, returning them as a tuple.

        Safely handles cases where the stack has fewer than two
        elements, returning 0 for missing values. The first returned
        value is the top element, the second is the next element.

        Returns:
            Tuple (top, second) where:
            - Both elements if stack has 2+ elements
            - (top, 0) if stack has 1 element
            - (0, 0) if stack is empty

        Example:
            ```
            >>> stack = Stack()
            >>> stack.push(10)
            >>> stack.push(20)
            >>> stack.pop_two()
            (20, 10)
            >>> stack.push(10)
            >>> stack.pop_two()
            (10, 0)
            >>> stack.pop_two()
            (0, 0)
            ```
        """
        if self.size() == 1:
            return self.pop(), 0
        if self.size() == 0:
            return 0, 0
        return self.pop(), self.pop()
    
    def stack_swap(self) -> None:
        """
        Swap the positions of the top two elements on the stack.

        Implements the Befunge `\\` operation. If the stack has
        fewer than two elements, missing values are treated as 0.

        Behavior:
        - 2+ elements: Swaps the top two elements
        - 1 element: Pushes 0, so stack becomes [original, 0]
        - 0 elements: Pushes two zeroes: [0, 0]
        """
        if self.size() == 1:
            self.push(0)
        b, a = self.pop_two()
        self.push(b)
        self.push(a)