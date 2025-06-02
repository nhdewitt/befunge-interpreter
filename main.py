from Stack import Stack
from InstructionPointer import InstructionPointer, IPDebug
from visualizer import BefungeDisplay
import dispatch_table

R_DIRECTION = ["up", "down", "left", "right"]

def interpret_steps(code):
    """Generator that yields a tuple on each iteration:
    (grid, ip_x, ip_y, direction, stack_contents, current_output)
    When @ is reached, stop
    """
    stack = Stack()
    ip = InstructionPointer(code)
    output = ""
    ip.waiting_for = None
    ip.pending_input = None
    ip.last_was_random = False
    current_grid = ip.grid[ip.y][ip.x]

    while current_grid != "@":
        if current_grid == '"':
            ip.string = not ip.string
        elif ip.string:
            stack.push(ord(current_grid))
        
        elif current_grid == ' ':
            pass

        else:
            handler = dispatch_table.dispatch.get(current_grid)
            if handler:
                potential_output = handler(ip, stack, output)
                if isinstance(potential_output, str):
                    output = potential_output

        if ip.waiting_for is not None:
            yield ip, list(stack), output

            while ip.pending_input is None:
                yield None

            stack.push(ip.pending_input)
            ip.pending_input = None
            ip.waiting_for = None

        ip.x, ip.y = ip.move()

        yield ip, list(stack), output

        current_grid = ip.grid[ip.y][ip.x]
        continue

    # Yield final @ state:
    yield ip, list(stack), output


def main():
    import sys

    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "test.bf"
    
    try:
        with open(filename, 'r') as f:
            content = f.read().splitlines()
    except:
        print(f"{filename} not found.")
        return
    
    code_grid = [list(line) for line in content]
    max_width = max(len(row) for row in code_grid)
    code_grid = [row + [' '] * (max_width - len(row)) for row in code_grid]
    
    interpreter_gen = interpret_steps(code_grid)

    display = BefungeDisplay(code_grid)
    display.run(interpreter_gen)  # Pass the generator to the display

if __name__ == "__main__":
    main()