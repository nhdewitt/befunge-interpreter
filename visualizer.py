import curses
import time

class BefungeDisplay:
    def __init__(self, grid):
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0])

    def run(self, interpreter_gen):
        """Run the interpreter generator and display the grid."""
        curses.wrapper(self._curses_main, interpreter_gen)

    def _curses_main(self, stdscr, interpreter_gen):
        """Main function for curses display."""
        curses.curs_set(0)  # Hide the cursor
        curses.start_color()

        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)

        stdscr.clear()
        stdscr.nodelay(True)  # Make getch non-blocking
        stdscr.timeout(0)  # Refresh every 50 ms

        last_state = None

        for state in interpreter_gen:
            if state is None:
                _ = stdscr.getch()
                time.sleep(0.025)
                continue
            ip, stack, output = state
            last_state = state

            if ip.waiting_for == "int":
                value = self._prompt_for_int(stdscr)
                ip.pending_input = value
                continue

            elif ip.waiting_for == "char":
                value = self._prompt_for_char(stdscr)
                ip.pending_input = value
                continue

            self.draw(
                stdscr,
                ip.grid,
                ip.x, ip.y,
                ip.direction,
                ip.last_was_random,
                stack,
                output
            )

            c = stdscr.getch()
            if c == ord('q'):
                return
            time.sleep(0.025)


        if last_state is not None:
            ip, stack, output = last_state
            self.draw(
                stdscr,
                ip.grid,
                ip.x, ip.y,
                ip.direction,
                ip.last_was_random,
                stack,
                output
            )

        stdscr.nodelay(False)  # Reset to blocking mode
        stdscr.timeout(-1)

        prompt_row = min(self.height + 1, curses.LINES - 1)

        stdscr.move(prompt_row, 0)
        stdscr.clrtoeol()
        stdscr.addstr(prompt_row, 0, "Press any key to exit...", curses.A_BOLD)
        stdscr.refresh()
        stdscr.getch()

    def _prompt_for_int(self, stdscr):
        """Prompt the user for an integer input, block until 0-9 is entered."""
        height_screen, width_screen = stdscr.getmaxyx()
        prompt = "Enter a digit (0-9): "
        prompt_row = min(self.height + 1, height_screen - 1)

        while True:
            stdscr.move(prompt_row, 0)
            stdscr.clrtoeol()
            stdscr.addstr(prompt_row, 0, prompt, curses.color_pair(3) | curses.A_BOLD)
            stdscr.refresh()

            c = stdscr.getch()
            if c == -1:
                time.sleep(0.01)
                continue
            if ord('0') <= c <= ord('9'):
                return c - ord('0')
            
    def _prompt_for_char(self, stdscr):
        """Prompt the user for a character input, block until a character is entered."""
        height_screen, width_screen = stdscr.getmaxyx()
        prompt = "Enter a character: "
        prompt_row = min(self.height + 1, height_screen - 1)

        while True:
            stdscr.move(prompt_row, 0)
            stdscr.clrtoeol()
            stdscr.addstr(prompt_row, 0, prompt, curses.color_pair(3) | curses.A_BOLD)
            stdscr.refresh()

            c = stdscr.getch()
            if c == -1:
                time.sleep(0.01)
                continue
            return c

    def draw(self, stdscr, grid, ip_x, ip_y, direction, last_was_random, stack, output):
        """Draw the grid and the IP."""
        for row_idx, row in enumerate(grid):
            for col_idx, ch in enumerate(row):
                if ch is None or ch == '\x00':
                    ch = ' '

                if (col_idx, row_idx) == (ip_x, ip_y):
                    # Highlight the IP (reverse video + color)
                    stdscr.addstr(row_idx, col_idx, ch, 
                                  curses.color_pair(2) | curses.A_STANDOUT | curses.A_BOLD)
                else:
                    stdscr.addstr(row_idx, col_idx, ch,
                                  curses.color_pair(1))

        height_screen, width_screen = stdscr.getmaxyx()
        grid_bottom = self.height
        if grid_bottom < height_screen:
            stdscr.hline(grid_bottom, 0, curses.ACS_HLINE, min(self.width, width_screen),
                         curses.color_pair(3))
        
        info_row = self.height + 1
        stdscr.move(info_row, 0)
        stdscr.clrtoeol()
        if last_was_random:
            stdscr.addstr(info_row, 0, f"Direction {direction.title()} (random)  IP: ({ip_x}, {ip_y})  ", curses.A_BOLD)
        else:
            stdscr.addstr(info_row, 0, f"Direction: {direction.title()}  IP: ({ip_x}, {ip_y})  ", curses.A_BOLD)

        stdscr.move(info_row + 1, 0)
        stdscr.clrtoeol()
        stdscr.addstr(info_row + 1, 0, "Stack: " + " ".join(str(v) for v in stack))

        height_screen, width_screen = stdscr.getmaxyx()
        out_lines = output.split('\n')
        last_three = out_lines[-3:] if len(out_lines) > 3 else out_lines

        for i in range(3):
            row = info_row + 2 + i
            if row >= height_screen:
                break

            stdscr.move(row, 0)
            stdscr.clrtoeol()

            if i < len(last_three):
                line = last_three[i]
                # Remove null characters
                safe_line = line.replace('\0', '')
                stdscr.addstr(row, 0, safe_line[:width_screen - 1])

        stdscr.refresh()