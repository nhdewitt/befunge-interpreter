class Stack:
    def __init__(self):
        self.items = []

    def __repr__(self):
        return f"Size: {self.size()} - Stack: {self.items}"
    
    def push(self, item):
        self.items.append(item)

    def size(self):
        return len(self.items)
    
    def peek(self):
        """Return top of stack without popping"""
        return self.items[-1] if self.items else None
    
    def pop(self):
        """Pop stack, 0 if empty"""
        return self.items.pop() if self.size() > 0 else 0
    
    def pop_two(self):
        """Pop two off the stack, if less than two one stack, return 0"""
        if self.size() == 1:
            return self.pop(), 0
        if self.size() == 0:
            return 0, 0
        return self.pop(), self.pop()
    
    def stack_swap(self):
        """Pop two and swap positions on stack"""
        if self.size() == 1:
            self.push(0)
        b, a = self.pop_two()
        self.push(b)
        self.push(a)