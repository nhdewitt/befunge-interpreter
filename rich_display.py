from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.style import Style
from rich.text import Text
import time
import sys

class RichBefungeDisplay:
    def __init__(self, grid, frame_delay: float = 0.5):
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0])
        self.console = Console()
        self.frame_delay = frame_delay

    def run(self, interpreter_gen):
        self.console.clear()
        """
        Run the interpreter generator and display the grid using Rich Live
        Yield will either be:
        None (sleep)
        (ip, stack, output) tuples with:
            - ip.grid - current 2D list of characters
            - ip.x, ip.y - current position of the instruction pointer
            - ip.direction - string ("up", "down", "left", "right")
            - ip.last_was_random - boolean indicating if the last instruction was random
            - ip.waiting_for - string ("int", "char") if waiting for input
            - stack - a list of integers in the stack
            - output - the output text
        """
        last_state = None       # Store the last state to show the final snapshot before exit

        def make_renderable(state):
            """Build a single renderable object for Live"""
            ip, stack, output = state
            grid_render         = self._render_grid(ip.grid, ip.x, ip.y)
            sep                 = Rule(style="white")
            info                = self._render_info(ip.direction, ip.last_was_random, ip.x, ip.y)
            stack_line          = Text("Stack: " + " ".join(str(v) for v in stack), style="bold white")
            out_panel           = self._render_output(output)

            return Panel(
                Group(
                    grid_render,
                    sep,
                    info,
                    stack_line,
                    out_panel
                ),
                border_style="bright_blue",
                padding=(1, 1),
                expand=True,
            )
        live = Live(console=self.console, refresh_per_second=10, screen=True)
        live.start()

        try:
            for state in interpreter_gen:
                if state is None:
                    time.sleep(self.frame_delay)
                    continue

                ip = state[0]

                if ip.waiting_for == "int":
                    live.stop()
                    ip.pending_input = self._prompt_for_int()
                    ip.waiting_for = None
                    live.start()
                    continue

                if ip.waiting_for == "char":
                    live.stop()
                    ip.pending_input = self._prompt_for_char()
                    ip.waiting_for = None
                    live.start()
                    continue

                last_state = state
                live.update(make_renderable(state))
                time.sleep(self.frame_delay)
            
            if last_state is not None:
                live.update(make_renderable(last_state))

            live.stop()
            self.console.print()
            self.console.print(
                Text("Press Enter to exit...", style="bold yellow"),
                justify="center"
            )
            input()

        finally:
            live.stop()

    def _render_grid(self, grid, ip_x, ip_y):
        """Build a single Text object that represents the entire grid, with the IP cell highlighted"""
        rows = []
        for y, row in enumerate(grid):
            line = Text(no_wrap=True)
            for x, char in enumerate(row):
                if char is None or char == "\x00":
                    char = " "
                style = Style(color="white", bgcolor="green", bold=True) \
                            if (x, y) == (ip_x, ip_y) \
                            else Style(color="red")
                line.append(char, style=style)
            rows.append(line)
        return Group(*rows)
    
    def _render_info(self, direction, last_was_random, ip_x, ip_y):
        """Render the direction and IP coordinates"""
        style = "bold white"
        if last_was_random:
            info_str = f"[bold red]Direction[/] {direction.title()} (random) IP: ({ip_x}, {ip_y})"
        else:
            info_str = f"[bold red]Direction:[/] {direction.title()} IP: ({ip_x}, {ip_y})"
        return Text.from_markup(info_str, style=style)
    
    def _render_output(self, output):
        """Take the full output string, split into lines, grab the last 3 and render as a single Text block"""
        out_lines = output.split('\n')
        last_three = out_lines[-3:] if len(out_lines) >= 3 else out_lines
        text = Text()
        for line in last_three:
            safe_line = line.replace("\x00", "")
            text.append(safe_line + "\n", style="white")
        return Panel(text, title="Output (last 3 lines)", border_style="bright_black")
    
    def _prompt_for_int(self):
        """Block until user enters a digit 0-9"""
        while True:
            try:
                inp = input("Enter a digit (0-9): ").strip()
            except (EOFError, KeyboardInterrupt):
                sys.exit(0)
            if len(inp) == 0:
                continue
            
            c = inp[0]
            if '0' <= c <= '9':
                return int(c)
            
            continue
            
    def _prompt_for_char(self):
        """Block until user enters a character, return just the first character if > 9"""
        try:
            inp = input("Enter a character: ")
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
        
        if len(inp) == 0:
            return 10
        return ord(inp[0])