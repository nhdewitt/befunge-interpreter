from Stack import Stack
from BefungeCode import BefungeCode
import lambdas as L

R_DIRECTION = ["up", "down", "left", "right"]

def interpret(code):
    stack = Stack()
    code = BefungeCode(code)
    output = ""
    current_grid = code.grid[code.y][code.x]

    while current_grid != "@":
        if current_grid == '"':
            code.string = not code.string
        elif code.string:
            stack.push(ord(current_grid))
        elif current_grid == ' ':
            pass
        elif current_grid in {'>','<','^','v','?'}:
            code.move(current_grid)
        elif current_grid.isdigit():
            stack.push(int(current_grid))
        elif current_grid == "+":
            b, a = stack.pop_two()
            stack.push(L.add(a, b))
        elif current_grid == "-":
            b, a = stack.pop_two()
            stack.push(L.sub(a, b))
        elif current_grid == "*":
            b, a = stack.pop_two()
            stack.push(L.mul(a, b))
        elif current_grid == "/":
            b, a = stack.pop_two()
            stack.push(L.div(a, b))
        elif current_grid == "%":
            b, a = stack.pop_two()
            stack.push(L.mod(a, b))
        elif current_grid == "!":
            a = stack.pop()
            stack.push(L.l_not(a))
        elif current_grid == "`":
            b, a = stack.pop_two()
            stack.push(L.gt(a, b))
        elif current_grid == "_":
            code.direction = "right" if stack.pop() == 0 else "left"
        elif current_grid == "|":
            code.direction = "down" if stack.pop() == 0 else "up"
        elif current_grid == ":":
            stack.push(0 if stack.size() == 0 else stack.peek())
        elif current_grid == "\\":
            a = stack.pop()
            b = stack.pop()
            stack.push(a)
            stack.push(b)
        elif current_grid == "$":
            stack.pop()
        elif current_grid == ".":
            output += str(stack.pop())
        elif current_grid == ",":
            output += chr(stack.pop())
        elif current_grid == "#":
            code.skip = True
        elif current_grid == "p":
            a = stack.pop()
            b = stack.pop()
            v = stack.pop()
            code.grid[a][b] = chr(v)
        elif current_grid == "g":
            a = stack.pop()
            b = stack.pop()
            stack.append(ord(code.grid[a][b]))
    
        code.steps = 2 if code.skip else 1
        if code.direction == "right":
            code.x += code.steps
        elif code.direction == "left":
            code.x -= code.steps
        elif code.direction == "up":
            code.y -= code.steps
        elif code.direction == "down":
            code.y += code.steps
        if code.y < 0:
            code.y += len(code.grid)
        elif code.y == len(code.grid):
            code.y = 0
        if code.x < 0:
            code.x += len(code.grid[0])
        elif code.x == len(code.grid[0]):
            code.x = 0

        code.skip = False
    
    return output