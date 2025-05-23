from Stack import Stack
from InstructionPointer import InstructionPointer, IPDebug
import lambdas as L
from display import BefungeDisplay  # Changed from visualizer import
import sys
import time

R_DIRECTION = ["up", "down", "left", "right"]

def interpret(code):
    cycles = 0
    debug = False
    stack = Stack()
    if debug:
        code = IPDebug(code)
    else:
        code = InstructionPointer(code)
    output = ""
    last = None
    current_grid = code.grid[code.y][code.x]

    while current_grid != "@":
        
        if debug:
            print(output)
            print(stack)

        if current_grid == '"':
            code.string = not code.string

        elif code.string:
            stack.push(ord(current_grid))

        elif current_grid == ' ':
            pass

        elif current_grid in {'>','<','^','v','?','#'}:
            if current_grid == '#':
                code.skip = True
            code.change_direction(current_grid)

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
            val = stack.pop()
            # Skip null characters and handle printable ASCII only
            if val > 0 and val < 128:
                char = chr(val)
                output += char
                print(f"DEBUG: Added char to output: {char!r}")
            else:
                print(f"DEBUG: Skipped non-printable character: {val}")

        elif current_grid == "p":
            y = stack.pop()
            x = stack.pop()
            v = stack.pop()
            # edge wrapping
            height = len(code.grid)
            width = len(code.grid[0])
            x = x % width
            y = y % height
            code.grid[y][x] = chr(v)

        elif current_grid == "g":
            y = stack.pop()
            x = stack.pop()
            # edge wrapping
            height = len(code.grid)
            width = len(code.grid[0])
            x = x % width
            y = y % height
            stack.push(ord(code.grid[y][x]))

        elif current_grid == "&":
            while True:                     # restrict input to one digit, re-prompt if invalid
                raw = input(output)
                if len(raw) != 1:
                    raw = raw[0]
                if not raw.isdigit():
                    continue
                else:
                    break
            stack.push(int(raw))
            output = ""

        elif current_grid == "~":           # restrict input to one character
            raw = input(output)
            if len(raw) != 1:
                raw = raw[0]
            stack.push(ord(raw))

        code.x, code.y = code.move()
        current_grid = code.grid[code.y][code.x]
        if output and output != last:
            if output[-1] == '\n':
                print(output, end="")       # flush the buffer with each newline
                output = ""
            else:
                print(output, end="\r")     # rewrite the line
        last = output
        cycles += 1
        time.sleep(0.0005)
    
    if debug:
        output += f" Cycles: {cycles}"
    print(output)
    return

def interpret_gen(code, display=None):  # Add display parameter
    print("DEBUG: Starting interpret_gen")
    cycles = 0
    debug = False
    stack = Stack()
    if debug:
        code = IPDebug(code)
    else:
        code = InstructionPointer(code)
    output = ""
    last = None
    current_grid = code.grid[code.y][code.x]
    print(f"DEBUG: Initial grid value: {current_grid!r}")

    while current_grid != "@":
        # Process current instruction
        if current_grid == '"':
            code.string = not code.string
        elif code.string:
            stack.push(ord(current_grid))

        elif current_grid == ' ':
            pass

        elif current_grid in {'>','<','^','v','?','#'}:
            if current_grid == '#':
                code.skip = True
            code.change_direction(current_grid)

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
            val = stack.pop()
            # Skip null characters and handle printable ASCII only
            if val > 0 and val < 128:
                char = chr(val)
                output += char
                print(f"DEBUG: Added char to output: {char!r}")
            else:
                print(f"DEBUG: Skipped non-printable character: {val}")

        elif current_grid == "p":
            y = stack.pop()
            x = stack.pop()
            v = stack.pop()
            # edge wrapping
            height = len(code.grid)
            width = len(code.grid[0])
            x = x % width
            y = y % height
            code.grid[y][x] = chr(v)

        elif current_grid == "g":
            y = stack.pop()
            x = stack.pop()
            # edge wrapping
            height = len(code.grid)
            width = len(code.grid[0])
            x = x % width
            y = y % height
            stack.push(ord(code.grid[y][x]))

        elif current_grid == "&":
            if display:
                display.update_output("Enter a number: ")
                display.refresh()
            while True:
                try:
                    raw = display.get_input() if display else input(output)
                    num = int(raw)  # Convert to integer
                    stack.push(num)
                    break
                except ValueError:
                    continue
            output = ""  # Clear output after input

        elif current_grid == "~":
            if display:
                display.update_output("Enter a character: ")
                display.refresh()
            raw = display.get_input() if display else input(output)
            if len(raw) != 1:
                raw = raw[0]
            stack.push(ord(raw))

        code.x, code.y = code.move()
        current_grid = code.grid[code.y][code.x]
        if output and output != last:
            if display:
                display.update_output(output)
            yield output
            last = output
        
        # Update display at end of cycle
        if display:
            display.cursor_pos = (code.x, code.y)
            display.stack = stack.items.copy()
            display.refresh()
            time.sleep(0.1)  # Adjust speed here
        
        cycles += 1
    
    print(f"DEBUG: Final output before exit: {output!r}")
    yield output

#  def main():
#     Quine
#     interpret("01->1# +# :# 0# g# ,# :# 5# 8# *# 4# +# -# _@")
#     FizzBuzz (https://github.com/kagof/BefungeRepo/blob/master/FizzBuzz.bf)
#     interpret('>66*4-,1+:35*%!#v_:3%!#v_:5%#v_v\n         v            0<       0\n  v        <v<v                <\n           """" 0               \n  v"fizz"<"buzz"<               \n  v,_v     """"                 \n  >:^$     ^<^<                 \n^    <                    .: < ')
#     Factorial (https://github.com/kagof/BefungeRepo/blob/master/Factorial.bf)
#     interpret('<v"Input a number: "\n v,<\n >:|\n   >&:.:05p>   :1-:#v_v\n           ^p50*g50:< >52*," :rewsnA",,,,,,,,05g.@')
#     HelloWorld (https://github.com/kagof/BefungeRepo/blob/master/HelloWorld.bf)
#     interpret('66*2*92+9*2+>       92*6*vv  \n  v2+1*9+49<^p0+1*46+8*96<4  \n< >9*1+2pv ^*7+98*48-1*4*7<  \n^       4<v6*6+1*29<         \n v+19<*3*6<>,v               \n >:*92+3*92+0p91+0p90p80p7v  \nv  p00p01p02p03p04p05p06p0<  \n>92+0g91+0g90g80g70g60g50gv  \n       v!:<g00g01g02g03g04<  \n      @_, ^                 ')

def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as file:
                content = file.read()
                # Convert content to 2D grid
                code_grid = [list(line) for line in content.splitlines()]
                # Pad rows to equal length
                max_width = max(len(row) for row in code_grid)
                code_grid = [row + [' '] * (max_width - len(row)) for row in code_grid]
                
                display = BefungeDisplay(code_grid)
                display.run(lambda code: interpret_gen(code, display))  # Pass display to interpreter
        except FileNotFoundError:
            print(f"{filename} not found.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        with open("test.bf", 'r') as file:
            content = file.read()
            interpret(content)

main()