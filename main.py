import sys
from Stack import Stack
from InstructionPointer import InstructionPointer, IPDebug
#from visualizer import BefungeDisplay
from rich_display import RichBefungeDisplay
import dispatch_table

R_DIRECTION = ["up", "down", "left", "right"]

def load_befunge_grid_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    max_width = max(len(line) for line in lines)
    grid = [list(line.ljust(max_width, " ")) for line in lines]
    return grid

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
    if len(sys.argv) != 2:
        print("Usage: python main.py <befunge_file>")
        sys.exit(1)
    else:
        path = sys.argv[1]

    grid = load_befunge_grid_from_file(path)
    interpreter = interpret_steps(grid)
    display = RichBefungeDisplay(grid)
    display.run(interpreter)

if __name__ == "__main__":
    main()