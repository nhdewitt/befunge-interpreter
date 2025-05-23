import curses
import sys
from typing import List, Tuple

class BefungeDisplay:
    def __init__(self, code: List[List[str]]):
        self.code = code
        self.height = len(code)
        self.width = len(code[0])
        self.output_lines = ["", ""]
        self.stack = []
        self.cursor_pos = (0, 0)
        self.stdscr = None
        self.code_win = None
        self.stack_win = None
        self.output_win = None

    def run(self, interpret_fn):
        curses.wrapper(self._main, interpret_fn)

    def _init_windows(self):
        # Setup colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        # Hide cursor and disable input echo
        curses.curs_set(0)
        curses.noecho()

        # Get screen dimensions
        screen_height, screen_width = self.stdscr.getmaxyx()

        # Create windows with padding for borders
        self.code_win = curses.newwin(self.height + 4, self.width + 4, 
                                     (screen_height - self.height) // 2 - 2, 
                                     (screen_width - self.width - 24) // 2)
        
        self.stack_win = curses.newwin(self.height + 4, 20, 
                                      (screen_height - self.height) // 2 - 2,
                                      (screen_width + self.width - 16) // 2)
        
        self.output_win = curses.newwin(6, screen_width - 4, 
                                       screen_height - 8,
                                       2)

    def _main(self, stdscr, interpret_fn):
        self.stdscr = stdscr
        self._init_windows()
        
        # Run interpreter
        gen = interpret_fn(''.join(''.join(row) for row in self.code))
        
        try:
            while True:
                # Draw code grid
                self.code_win.clear()
                self.code_win.border()
                self.code_win.addstr(0, 2, " Code ", curses.A_BOLD)
                for y, row in enumerate(self.code):
                    for x, char in enumerate(row):
                        try:
                            if (x, y) == self.cursor_pos:
                                self.code_win.addstr(y + 2, x + 2, char, curses.color_pair(2))
                            else:
                                self.code_win.addstr(y + 2, x + 2, char, curses.color_pair(1))
                        except curses.error:
                            pass
                self.code_win.refresh()

                # Draw stack
                self.stack_win.clear()
                self.stack_win.border()
                self.stack_win.addstr(0, 2, " Stack ", curses.A_BOLD)
                for i, val in enumerate(self.stack[-10:]):
                    try:
                        self.stack_win.addstr(i + 2, 2, f"{val:3}", curses.color_pair(3))
                    except curses.error:
                        pass
                self.stack_win.refresh()

                # Draw output
                self.output_win.clear()
                self.output_win.border()
                self.output_win.addstr(0, 2, " Output ", curses.A_BOLD)
                try:
                    self.output_win.addstr(2, 2, self.output_lines[0])
                    self.output_win.addstr(3, 2, self.output_lines[1])
                except curses.error:
                    pass
                self.output_win.refresh()

                # Update state
                try:
                    output = next(gen)
                    if output:
                        self.output_lines[0] = self.output_lines[1]
                        self.output_lines[1] = output
                except StopIteration:
                    break

                curses.napms(100)  # Delay for visibility

        except KeyboardInterrupt:
            pass

    def get_input(self) -> str:
        """Get single character input from user"""
        curses.echo()
        self.output_win.addstr(4, 2, "> ")
        self.output_win.refresh()

        # Get input until valid
        while True:
            try:
                # Get raw input (up to 3 chars to handle multi-digit numbers)
                raw = self.output_win.getstr(4, 4, 3).decode('utf-8').strip()
                
                # Clear input line
                self.output_win.addstr(4, 2, " " * 20)
                self.output_win.refresh()
                
                curses.noecho()
                return raw
                
            except (curses.error, UnicodeDecodeError):
                # Clear line and try again
                self.output_win.addstr(4, 2, " " * 20)
                self.output_win.refresh()
                continue

    def update_output(self, text: str) -> None:
        """Update the output display with new text"""
        if text:
            self.output_lines[0] = self.output_lines[1]
            self.output_lines[1] = text

    def refresh(self) -> None:
        """Force a screen refresh"""
        pass  # Not needed since windows refresh in _main