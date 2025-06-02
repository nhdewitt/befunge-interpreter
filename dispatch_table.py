import lambdas as L

def _binary_op(stack, op):
    """Pop two values, apply op(a, b), push the result."""
    b, a = stack.pop_two()
    stack.push(op(a, b))

def _direction_op(code, ch):
    """Change direction; if ch == '#', also set skip=True."""
    if ch == "#":
        code.skip = True
        return
    code.change_direction(ch)

def _conditional_horizontal(stack, code):
    """pop, go right if zero, else left"""
    code.direction = "right" if stack.pop() == 0 else "left"

def _conditional_vertical(stack, code):
    """pop, go down if zero, else up"""
    code.direction = "down" if stack.pop() == 0 else "up"

def _duplicate_top(stack):
    """duplicate top or push 0 if empty"""
    stack.push(0 if stack.size() == 0 else stack.peek())

def _swap_top_two(stack):
    """swap top two stack entries"""
    a = stack.pop()
    b = stack.pop()
    stack.push(a)
    stack.push(b)

def _pop_discard(stack):
    """pop and discard"""
    stack.pop()

def _output_int(stack, output):
    """pop an integer and append its string representation to output"""
    output += str(stack.pop())
    return output

def _output_char(stack, output):
    """pop a value and print if valid ASCII"""
    val = stack.pop()
    #if 0 < val < 128:
    #    output += chr(val)
    #else:
    #    pass
    output += chr(val)
    return output

def _put_grid(code, stack):
    """pop y, x, v, write chr(v) into code.grid[y][x]"""
    y = stack.pop() if stack else 0
    x = stack.pop() if stack else 0
    v = stack.pop() if stack else 0
    y = y if isinstance(y, int) else 0
    x = x if isinstance(x, int) else 0
    v = v if isinstance(v, int) else 0
    #edge wrapping
    height = len(code.grid)
    width = len(code.grid[0]) if height else 0
    x = (x % width) if width else 0
    y = (y % height) if height else 0
    code.grid[y][x] = chr(v)

def _get_grid(code, stack):
    """pop y, x and push ord(code.grid[y][x])"""
    y = stack.pop() if stack else 0
    x = stack.pop() if stack else 0
    y = y if isinstance(y, int) else 0
    x = x if isinstance(x, int) else 0
    #edge wrapping
    height = len(code.grid)
    width = len(code.grid[0])
    x = (x % width) if width else 0
    y = (y % height) if height else 0
    stack.push(ord(code.grid[y][x]))

def _mark_int_input(code, stack, output):
    """Flag for integer input"""
    code.waiting_for = "int"
    return None

def _mark_char_input(code, stack, output):
    """Flag for character input"""
    code.waiting_for = "char"
    return None

dispatch = {
    #Movement
    ">": lambda code, stack, output: _direction_op(code, ">"),
    "<": lambda code, stack, output: _direction_op(code, "<"),
    "^": lambda code, stack, output: _direction_op(code, "^"),
    "v": lambda code, stack, output: _direction_op(code, "v"),
    "?": lambda code, stack, output: _direction_op(code, "?"),
    "#": lambda code, stack, output: _direction_op(code, "#"),

    #Arithmetic
    "+": lambda code, stack, output: _binary_op(stack, L.add),
    "-": lambda code, stack, output: _binary_op(stack, L.sub),
    "*": lambda code, stack, output: _binary_op(stack, L.mul),
    "/": lambda code, stack, output: _binary_op(stack, L.div),
    "%": lambda code, stack, output: _binary_op(stack, L.mod),

    #Logicals
    "!": lambda code, stack, output: stack.push(L.l_not(stack.pop())),
    "`": lambda code, stack, output: _binary_op(stack, L.gt),

    #Conditionals
    "_": lambda code, stack, output: _conditional_horizontal(stack, code),
    "|": lambda code, stack, output: _conditional_vertical(stack, code),

    #Stack Manipulation
    ":": lambda code, stack, output: _duplicate_top(stack),
    "\\": lambda code, stack, output: _swap_top_two(stack),
    "$": lambda code, stack, output: _pop_discard(stack),

    #Output
    ".": lambda code, stack, output: _output_int(stack, output),
    ",": lambda code, stack, output: _output_char(stack, output),

    #Grid Manipulation
    "p": lambda code, stack, output: _put_grid(code, stack),
    "g": lambda code, stack, output: _get_grid(code, stack),

    #User Input
    "&": lambda code, stack, output: _mark_int_input(code, stack, output),
    "~": lambda code, stack, output: _mark_char_input(code, stack, output),
}

for d in "0123456789":
    dispatch[d] = (lambda code, stack, output, d=d: stack.push(int(d)))