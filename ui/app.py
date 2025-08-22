"""Befunge interpreter GUI application (Tkinter).

Provides a development environment for debugging and executing Befunge programs
with real-time visualization, interactive debugging, and opcode tooltips.

Key features:
  - Real-time code visualization with IP tracking and syntax highlighting.
  - Interactive debugging with breakpoints and step-by-step execution.
  - Separate output window with stack visualization and smart docking.
  - Comprehensive opcode tooltips with hover system.
  - Per-file settings persistence (speed, breakpoints).
  - Asynchronous input handling for Befunge input operations.
  - Configurable execution speed and batch processing.
  - File management with validation and error handling.
"""

import json
import os
import tempfile
from typing import Set, Tuple, Optional, Dict, Any
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.interpreter import Interpreter
from core.types import StepStatus, WaitTypes
from .opcode_hovertips import OpcodeHoverTip
from .opcodes import OPCODES, format_tooltip_for_opcode, compute_widths
from .format_stack import fmt_stack_item

# Pre-compute column widths for consistent tooltip formatting.
COL_WIDTHS = compute_widths(OPCODES)

# Cache tooltips that have already been generated.
TOOLTIP_CACHE: Dict[str, str] = {}

# Settings file format version for backward compatibility.
SETTINGS_VERSION = 2

# Default settings applied to new files on close.
DEFAULT_SETTINGS = {
    "version": SETTINGS_VERSION,
    "delay_ms": 50,         # ms between execution steps
    "steps_per_tick": 1,    # number of steps executed per timer tick
    "breakpoints": [],      # list of breakpoint coordinates
}

def tooltip_formatter(ch: str) -> str:
    """Return formatted tooltip text for a given character/opcode (cached).

    Args:
      ch: Single character to format a tooltip for.

    Caching:
      Tooltips are cached after first generation to improve hover responsiveness
      during repeated mouse movements over the same characters.
    """
    if ch not in TOOLTIP_CACHE:
        if ch.isdigit():
            # Digits push their numeric value onto the stack.
            TOOLTIP_CACHE[ch] = format_tooltip_for_opcode(
                ch,
                rows={ch: ("(push digit)", "", ch)},
                widths=COL_WIDTHS
            )
        elif ch == " ":
            # Spaces are no-ops.
            TOOLTIP_CACHE[ch] = format_tooltip_for_opcode(
                ch,
                rows={ch: ("(no-op)", "", "(no effect)")},
                widths=COL_WIDTHS
            )
        else:
            # Use main opcodes dict for all other characters.
            TOOLTIP_CACHE[ch] = format_tooltip_for_opcode(
                ch, rows=OPCODES, widths=COL_WIDTHS
            )

    return TOOLTIP_CACHE[ch]

class App(ttk.Frame):
    """Main GUI application for the Befunge interpreter.

    Window management:
      - Main editor window with syntax highlighting.
      - Detachable output window with docking.
      - Window state preservation.

    Execution control:
      - Variable speed execution (1–500 ms delays).
      - Batch processing (1–50 steps per tick).
      - Breakpoint-aware execution with pause/resume.
      - Asynchronous input handling for user interaction.

    Attributes:
      interp: The Befunge interpreter instance.
      speed_ms: IntVar controlling delay between execution steps.
      steps_per_tick: IntVar controlling batch size per timer tick.
      breakpoints: Set of (x, y) coordinates where execution should pause.
      current_path: Path to the currently loaded file (None if unsaved).
      last_dir: Last directory used for file operations.

    GUI components:
      text: Main Text widget displaying the Befunge grid.
      status: Label showing current interpreter state.
      input_bar: Frame containing input controls (hidden by default).
      _out_win: Optional Toplevel window for program output.
      _hover: OpcodeHoverTip instance for interactive tooltips.

    Settings management:
      _last_saved_settings: Cached settings for change detection.
      _settings_changed: Flag indicating unsaved settings changes.
      _suspend_setting_traces: Flag to prevent recursive setting updates.
    """
    def __init__(
            self,
            master: tk.Misc,
            interp: Interpreter,
            *,
            open_on_start: bool = True,
            **kwargs
        ) -> None:
        """Initialize the GUI application.

        Args:
          master: Parent Tkinter widget (usually the root window).
          interp: Befunge interpreter instance to control.
          open_on_start: Whether to show the file-open dialog on startup.
          **kwargs: Additional ttk.Frame options.

        Initialization sequence:
          1. Configure window close handler for graceful shutdown.
          2. Initialize application state and execution control.
          3. Set up output window management.
          4. Configure settings persistence.
          5. Build GUI components and event handlers.
          6. Initialize tooltip and visualization systems.
          7. Perform initial rendering and optional file opening.
        """
        super().__init__(master, **kwargs)

        # Configure window close handler.
        root = self.winfo_toplevel()
        root.protocol("WM_DELETE_WINDOW", self._on_app_close)

        # Core application state.
        self.interp = interp
        self._after: Optional[str] = None   # Timer ID for execution loop
        self._shown_output = False

        # Output window components (created on demand).
        self._out_win: Optional[tk.Toplevel] = None
        self._out_txt: Optional[tk.Text] = None
        self._out_len: int = 0  # Track output length for incremental updates
        self._out_autoscroll = tk.BooleanVar(value=True)
        self._stack_lb: Optional[tk.Listbox] = None

        # Execution control settings.
        self.speed_ms = tk.IntVar(value=DEFAULT_SETTINGS["delay_ms"])
        self.steps_per_tick = tk.IntVar(value=DEFAULT_SETTINGS["steps_per_tick"])
        self.breakpoints: Set[Tuple[int, int]] = set()

        # Display variables for real-time settings feedback.
        self._delay_text = tk.StringVar()
        self._steps_text = tk.StringVar()

        # Settings persistence state for per-file configuration.
        self._last_saved_settings: Dict[str, Any] = {
            "delay_ms": int(self.speed_ms.get()),
            "steps_per_tick": int(self.steps_per_tick.get()),
            "breakpoints": [],  # updated after settings load
        }
        self._settings_changed = False
        self._suspend_setting_traces = False

        # Monitor settings changes for auto-save.
        self.speed_ms.trace_add("write", self._reschedule_if_running)
        self.steps_per_tick.trace_add("write", self._on_settings_change)

        # File management state.
        self.current_path: Optional[str] = None
        self.last_dir: Optional[str] = None

        # Grid revision tracking for efficient GUI updates.
        self._last_grid_rev: int = -1

        # Output window docking system.
        self._dock_side: Optional[str] = None
        self._dock_gap: int = 12
        self._dock_bind_id: Optional[str] = None

        # Visual state tracking.
        self._last_ip_xy: Optional[Tuple[int, int]] = None

        # Build and configure GUI components.
        self._build()
        self._build_input_bar()
        self._bind()

        # Initial setup.
        if open_on_start:
            self.after_idle(self.open_file)
        self.after_idle(self.render)    # Display initial state

    def open_file(self) -> None:
        """Prompt the user to select and open a Befunge source file.

        Opens a file dialog defaulting to ./src, loads the selected file, and
        initializes the interpreter with the new code. Also loads any associated
        settings from a sidecar file.

        File dialog configuration:
          - Initial directory: ./src (created if missing).
          - Supported extensions: .bf, .befunge.
          - Basic file validation before loading.

        Error handling:
          - File access errors: error dialog with details.
          - Invalid file types: warning about supported formats.
          - Corrupted settings files: fallback to defaults.
        """
        try:
            os.makedirs("./src", exist_ok=True)
        except OSError as e:
            messagebox.showerror(
                f"Failed to create './src'",
                f"Could not create directory:\n{e}",
                parent=self.winfo_toplevel()
            )
        initial_dir = os.path.expanduser("./src")
        path = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            initialdir=initial_dir,
            title="Load Befunge file",
            filetypes=[("Befunge (*.bf, *.befunge)", "*.bf *.befunge")]
        )
        if not path:
            return
        
        # Save settings for current file before switching.
        self._save_sidecar_settings_if_changed()

        try:
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()
        except Exception as e:
            messagebox.showerror(
                f"Failed to open {path}",
                f"Could not open file:\n{e}",
                parent=self.winfo_toplevel()
                )
            return
        
        self.current_path = path
        self._load_sidecar_settings(path)
        self.load_file(src, path)
        
    def load_file(self, src: str, path: Optional[str] = None) -> None:
        """Load Befunge source code into the interpreter and update the GUI.

        Stops any running execution, loads the new source code, clears output, and
        refreshes the display. Can be called programmatically or from file ops.

        Args:
          src: Befunge source code as a string.
          path: Optional file path for title display and settings.
        """
        self.stop()
        self.interp.load(src)
        self._clear_output_text()
        self.render()

        self.current_path = path
        if path:
            self.last_dir = os.path.dirname(path)
        self._set_title()
        self._update_run_buttons()

    def _set_title(self) -> None:
        """Update window title to show the current filename."""
        root = self.winfo_toplevel()
        name = os.path.basename(self.current_path) if self.current_path else "(untitled)"
        root.title(f"Befunge - {name}")

    def open_output_window(self, clear: bool = True) -> None:
        """Open or focus the program output window.

        Creates a new output window if none exists, or brings the existing window
        to the foreground. The window shows program output and a live view of the
        execution stack.

        Args:
          clear: Whether to clear existing output when opening.

        Window layout:
          - Left pane (weight 4): scrollable text area for program output.
          - Right pane (weight 1): stack visualization (top down).
          - Bottom bar: controls for copy, save, clear, autoscroll.

        Smart docking:
          - Chooses position relative to main window (right, left, below).
          - Follows main window movement with a gap.
          - Preserves relative positioning across sessions.

        Output management:
          - Incremental updates for performance with large output.
          - Optional autoscroll.
          - Output truncation (last 100k characters when very large).
        """
        # Focus existing window if already open.
        if self._out_win and self._out_win.winfo_exists():
            try:
                if str(self._out_win.state()) == "iconic":
                    self._out_win.deiconify()
            except Exception:
                pass

            if clear:
                self._clear_output_text()
                self._refresh_stack_view()
                self._prefill_output_from_interpreter()
            return
        
        # Create new output window.
        win = tk.Toplevel(self)

        try:
            win.transient(None)
        except Exception:
            pass
        try:
            win.attributes("-topmost", False)
        except Exception:
            pass

        name = os.path.basename(self.current_path) if self.current_path else "(untitled)"
        win.title(f"{name} Output")
        win.resizable(True, True)

        content = ttk.Frame(win)
        content.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        # Horizontal paned window for output text and stack view.
        pw = ttk.Panedwindow(content, orient=tk.HORIZONTAL)
        pw.pack(fill="both", expand=True)

        # Left pane: Program output text with scrollbar.
        left = ttk.Frame(pw)
        txt = tk.Text(left, wrap=tk.WORD, font=("Consolas", 11), height=16)
        yscroll_out = ttk.Scrollbar(left, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(state=tk.DISABLED, yscrollcommand=yscroll_out.set)

        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        txt.grid(row=0, column=0, sticky=tk.NSEW)
        yscroll_out.grid(row=0, column=1, sticky=tk.NS)

        # Right pane: Stack visualization with scrollbar.
        right = ttk.Frame(pw, width=160)
        ttk.Label(right, text="Stack").pack(anchor=tk.W, padx=4, pady=(0, 4))
        lb = tk.Listbox(right, font=("Consolas", 11), activestyle=tk.NONE)
        yscroll_stack = ttk.Scrollbar(right, orient=tk.VERTICAL, command=lb.yview)
        lb.configure(yscrollcommand=yscroll_stack.set)

        lb.pack(side=tk.LEFT, fill="both", expand=True, padx=(4, 0), pady=(0, 4))
        yscroll_stack.pack(side=tk.LEFT, fill="y", padx=(0, 4), pady=(0, 4))

        pw.add(left, weight=4)  # Output gets majority of space.
        pw.add(right, weight=1) # Stack gets smaller portion.

        # Control bar at bottom.
        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=(6, 8))

        ttk.Checkbutton(bar, text="Autoscroll",
                        variable=self._out_autoscroll).pack(side=tk.LEFT)

        def copy_all() -> None:
            """Copy all program output to clipboard."""
            self.clipboard_clear()
            self.clipboard_append(self.interp.output)
        
        def save_to_file() -> None:
            """Save program output to a text file."""
            base = "Untitled"
            if self.current_path:
                base = os.path.splitext(os.path.basename(self.current_path))[0]
            default_name = base + ".txt"

            path = filedialog.asksaveasfilename(
                parent=win,
                title="Save output",
                initialdir=self.last_dir or (os.path.dirname(self.current_path) if self.current_path else "."),
                initialfile=default_name,
                defaultextension=".txt",
                filetypes=[("Text files (*.txt)", "*.txt"), ("All files (*.*)", "*.*")],
                confirmoverwrite=True,
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.interp.output)
        
        # Control buttons.
        ttk.Button(bar, text="Copy", command=copy_all).pack(side=tk.LEFT, padx=(8,0))
        ttk.Button(bar, text="Save...", command=save_to_file).pack(side=tk.LEFT, padx=6)
        ttk.Button(bar, text="Clear", command=self._clear_output_text).pack(side=tk.LEFT, padx=6)
        ttk.Button(bar, text="Close", command=win.destroy).pack(side=tk.RIGHT)

        # Store references for updates and state management.
        self._out_win = win
        self._out_txt = txt
        self._stack_lb = lb
        self._out_len = 0

        # Set up docking system.
        self._dock_side = self._choose_dock_side(win)
        self._place_docked(win)
        self._bind_follow_main(win)

        if clear:
            self._clear_output_text()
            self._prefill_output_from_interpreter()
        else:
            self._out_len = len(self.interp.output)

        def on_close() -> None:
            """Clean up references and event handlers when window is closed."""
            self._out_win = None
            self._out_txt = None
            self._stack_lb = None

            if self._dock_bind_id:
                try:
                    self.winfo_toplevel().unbind("<Configure>", self._dock_bind_id)
                except Exception:
                    pass
                self._dock_bind_id = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)

        # Initialize content with current state.
        if clear:
            self._clear_output_text()
        self._refresh_stack_view()

    def _choose_dock_side(self, win: tk.Toplevel) -> str:
        """Choose the optimal docking side for the output window.

        Prefers right side, with fallbacks based on available space.

        Args:
          win: The output window to position.

        Returns:
          "right", "left", or "below".
        """
        root = self.winfo_toplevel()
        root.update_idletasks()
        win.update_idletasks()

        sw = root.winfo_screenwidth()
        rx = root.winfo_rootx()
        rw = root.winfo_width()
        ww = win.winfo_reqwidth()

        # Prefer right, then left, then below.
        if rx + rw + self._dock_gap + ww <= sw:
            return "right"
        if rx - self._dock_gap - ww >= 0:
            return "left"
        return "below"
    
    def _place_docked(self, win: tk.Toplevel) -> None:
        """Position the output window relative to the main window.

        Args:
          win: The output window to position.

        Positioning logic:
          - Right: adjacent to right edge with a gap.
          - Left: adjacent to left edge with a gap.
          - Below: underneath the main window with a gap.
          - Boundary checking keeps the window on-screen.
        """
        if not (win and win.winfo_exists()):
            return
        
        root = self.winfo_toplevel()
        root.update_idletasks()
        win.update_idletasks()

        rx, ry = root.winfo_rootx(), root.winfo_rooty()
        rw, rh = root.winfo_width(), root.winfo_height()
        ww, wh = win.winfo_reqwidth(), win.winfo_reqheight()
        side = self._dock_side or "right"
        gap = self._dock_gap

        if side == "right":
            x, y = rx + rw + gap, ry
        elif side == "left":
            x, y = rx - ww - gap, ry
        else:
            x, y = rx, ry + rh + gap

        # Keep on screen.
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        x = max(0, min(x, sw - ww))
        y = max(0, min(y, sh - wh))

        win.geometry(f"+{x}+{y}")

    def _bind_follow_main(self, win: tk.Toplevel) -> None:
        """Make the output window follow the main window movement/resizing.

        Binds handlers so the docking position is maintained as the main window
        moves/resizes.

        Args:
          win: The output window to reposition when the main window changes.
        """
        if self._dock_bind_id:
            try:
                self.winfo_toplevel().unbind("<Configure>", self._dock_bind_id)
            except Exception:
                pass
            self._dock_bind_id = None

        def _on_cfg(_e=None):
            if win.winfo_exists():
                self._place_docked(win)

        self._dock_bind_id = self.winfo_toplevel().bind(
            "<Configure>", _on_cfg, add=True
        )

    def _refresh_stack_view(self) -> None:
        """Update the stack visualization in the output window.

        Displays stack contents from top to bottom in the listbox, with each item
        showing numeric value and ASCII character representation when applicable.
        """
        if not (self._out_win and self._stack_lb and self._out_win.winfo_exists()):
            return
        
        lb = self._stack_lb
        lb.delete(0, tk.END)

        # Display stack from top to bottom.
        items = list(self.interp.stack)
        for v in reversed(items):
            lb.insert(tk.END, fmt_stack_item(v))

    def _clear_output_text(self) -> None:
        """Clear the output text area and reset tracking variables."""
        self._out_len = 0
        if self._out_txt and self._out_txt.winfo_exists():
            self._out_txt.configure(state=tk.NORMAL)
            self._out_txt.delete("1.0", tk.END)
            self._out_txt.configure(state=tk.DISABLED)

    def _append_output_if_needed(self) -> None:
        """Append new output to the output window if the interpreter output grew.

        Appends only the new portion of output for performance. Also manages
        autoscroll and trims very large widgets.
        """
        if not (self._out_win and self._out_txt and self._out_win.winfo_exists()):
            return
        
        out = self.interp.output
        out_len = len(out)
        if out_len == self._out_len:
            return
        
        MAX_DISPLAY = 100_000

        if out_len > MAX_DISPLAY:
            if self._out_len == 0:
                # First display: show truncation message, then last MAX_DISPLAY.
                self._out_txt.configure(state=tk.NORMAL)
                self._out_txt.insert(
                    tk.END, f"[Output truncated - showing last {MAX_DISPLAY} chars]\n"
                )
                self._out_txt.insert(tk.END, out[-MAX_DISPLAY:])
                self._out_txt.configure(state=tk.DISABLED)
            else:
                # Append new portion.
                new_chunk = out[self._out_len:]
                self._out_txt.configure(state=tk.NORMAL)

                # If text widget is getting too large, trim from beginning.
                current_size = int(self._out_txt.index('end-1c').split('.')[0])
                if current_size > 10_000:
                    self._out_txt.delete('1.0', '100.0')    # Remove first 100 lines.

                self._out_txt.insert(tk.END, new_chunk)
                self._out_txt.configure(state=tk.DISABLED)
        else:
            # Normal append.
            new_chunk = out[self._out_len:]
            self._out_txt.configure(state=tk.NORMAL)
            self._out_txt.insert(tk.END, new_chunk)
            self._out_txt.configure(state=tk.DISABLED)

        self._out_len = out_len

        if self._out_autoscroll.get():
            self._out_txt.see(tk.END)

        self._refresh_stack_view()

    def _build(self) -> None:
        """Construct the main GUI layout (toolbar, editor, status bar, tooltips)."""
        # Toolbar with execution controls.
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=4)

        self.btn_open = ttk.Button(toolbar, text="Open... (Ctrl-O)", command=self.open_file)
        self.btn_run = ttk.Button(
            toolbar, text="Run (F5)", command=lambda: self.run(clear_output=True)
        )
        self.btn_step = ttk.Button(toolbar, text="Step (F10)", command=self.step_once)
        self.btn_stop = ttk.Button(toolbar, text="Stop (Esc)", command=self.stop)

        for w in (self.btn_open, self.btn_run, self.btn_step, self.btn_stop):
            w.pack(side=tk.LEFT, padx=4)

        # Execution speed controls.
        delay_group = ttk.Frame(toolbar)
        delay_group.pack(side=tk.LEFT, padx=(12, 10))
        ttk.Label(delay_group, text="Delay (ms)").pack(anchor=tk.CENTER)
        ttk.Label(delay_group, textvariable=self._delay_text).pack(anchor=tk.CENTER)
        ttk.Scale(
            delay_group, from_=1, to=500, variable=self.speed_ms,
            orient=tk.HORIZONTAL, length=140
        ).pack(anchor=tk.CENTER)

        steps_group = ttk.Frame(toolbar)
        steps_group.pack(side=tk.LEFT, padx=(12, 10))
        ttk.Label(steps_group, text="Steps/tick").pack(anchor=tk.CENTER)
        ttk.Label(steps_group, textvariable=self._steps_text).pack(anchor=tk.CENTER)
        ttk.Scale(
            steps_group, from_=1, to=50, variable=self.steps_per_tick,
            orient=tk.HORIZONTAL, length=160
        ).pack(anchor=tk.CENTER)

        # Main code display.
        self.text = tk.Text(
            self,
            width=80,
            height=25,
            font=("Consolas", 12),
            background="#011b04",
            fg="#44C553",
            wrap=tk.NONE
        )
        self.text.configure(setgrid=True, spacing1=0, spacing2=0, spacing3=0)
        self.text.pack(fill=tk.BOTH, expand=True)

        # Interactive tooltip system.
        self._hover = OpcodeHoverTip(
            self.text,
            formatter=tooltip_formatter,
            delay=250,
            interp=self.interp,
            cell_filter=lambda ch, x, y: (
                ch != "\n" and x < self.interp.ip.orig_width and y < self.interp.ip.orig_height
                )
        )     

        # Visual styling for debugging features.
        self.text.tag_configure(
            "bp",
            background="#ff6b3d",
            foreground="#011b04"
        )   # Breakpoints: orange-red
        self.text.tag_configure(
            "ip",
            background="#00d1a0",
            foreground="#011b04"
        )   # IP: mint
        self.text.tag_configure(
            "hover_cell",
            background="#0a2516",
            foreground="#4ed05d"
        )
        
        self.text.tag_raise("ip")
        self.text.tag_raise("bp")
        self.text.tag_raise("hover_cell")

        # Status bar.
        self.status = ttk.Label(self, anchor=tk.W)
        self.status.pack(fill=tk.X)

        # Bind delay/steps text.
        self._bind_value_labels()

        self._update_run_buttons()

    def _bind(self) -> None:
        """Set up keyboard shortcuts and mouse event handlers."""
        # Keyboard shortcuts.
        self.master.bind("<Control-o>", lambda e: self.open_file())
        self.master.bind("<F5>", lambda e: self.run())
        self.master.bind("<F10>", lambda e: self.step_once())
        self.master.bind("<Escape>", lambda e: self.stop())

        # Ctrl+LMB to toggle breakpoints.
        self.master.bind(
            "<Control-Button-1>",
            self._on_toggle_bp_click,
            add=True
        )

    def _bind_value_labels(self) -> None:
        """Display speed and steps/tick values next to configuration sliders."""
        def upd_delay(*_):
            self._delay_text.set(f"{int(self.speed_ms.get())}")

        def upd_steps(*_):
            self._steps_text.set(f"{int(self.steps_per_tick.get())}")

        upd_delay()
        upd_steps()

        self.speed_ms.trace_add("write", lambda *_: upd_delay())
        self.steps_per_tick.trace_add("write", lambda *_: upd_steps())

    def run(self, *, clear_output: bool = False) -> None:
        """Start continuous program execution.

        Begins automatic execution using a timer loop, opening the output window
        and optionally clearing previous output. Execution continues until the
        program halts, hits a breakpoint, or is manually stopped.

        Args:
          clear_output: Whether to clear previous output before starting.
        """
        self._cancel_timer()

        if self._program_is_empty():
            self.bell()
            self.status.config(text="No program is loaded")
            return
        
        # Ensure output window is open.
        self.open_output_window(clear=clear_output)

        # Pre-fill output if cleared to avoid inserting full backlog.
        if clear_output:
            self._prefill_output_from_interpreter()

        # Begin execution loop.
        self.tick()

    def _update_run_buttons(self) -> None:
        """Enable/disable run/step buttons based on whether a program is loaded."""
        empty = self._program_is_empty()
        state = tk.DISABLED if empty else tk.NORMAL
        self.btn_run.configure(state=state)
        self.btn_step.configure(state=state)

    def step_once(self) -> None:
        """Execute exactly one interpreter step and update the UI.

        Cancels any running timers, ensures the output window is visible, performs
        a single step, then refreshes the display. If the interpreter requests
        input, shows the input bar.
        """
        self._cancel_timer()

        if self._program_is_empty():
            self.bell()
            self.status.config(text="No program loaded")
            return

        # Ensure output window is open but don't clear.
        if not (self._out_win and self._out_win.winfo_exists()):
            self.open_output_window(clear=False)
            self._out_len = len(self.interp.output)

        status = self.interp.step()

        self.render()
        self._append_output_if_needed()

        if status is StepStatus.AWAITING_INPUT:
            self._show_input_bar()

    def tick(self) -> None:
        """Execute one batch of steps and schedule the next batch.

        Executes a configurable number of steps, checks for breakpoints, and
        schedules the next batch unless the program has halted or needs input.
        """
        status = StepStatus.RUNNING
        steps = int(self.steps_per_tick.get())

        for _ in range(steps):
            ip = self.interp.ip

            # Check for breakpoints before executing.
            if (ip.x, ip.y) in self.breakpoints:
                self._cancel_timer()
                self.status.config(
                    text=f"Paused at breakpoint ({ip.x},{ip.y})"
                )
                self.render()
                self._append_output_if_needed()
                return
            
            status = self.interp.step()
            if status is not StepStatus.RUNNING:
                break

        self.render()
        self._append_output_if_needed()

        if status is StepStatus.RUNNING:
            self._after = self.after(int(self.speed_ms.get()), self.tick)
        elif status is StepStatus.AWAITING_INPUT:
            self._show_input_bar()
        else:
            self._cancel_timer()
    
    def stop(self) -> None:
        """Stop automatic execution but keep the output window open."""
        self._cancel_timer()
        if hasattr(self, "input_bar"):
            self.input_bar.pack_forget()

    def _program_is_empty(self) -> bool:
        """Return True if no non-space chars appear within the original grid size."""
        ip = self.interp.ip
        if ip.orig_width == 0 or ip.orig_height == 0:
            return True        
        for y in range(ip.orig_height):
            row = ip.grid[y][:ip.orig_width]
            if any(ch != " " for ch in row):
                return False        
        return True

    def _reschedule_if_running(self, *_: object) -> None:
        """If a timer is active, cancel and reschedule it with the new delay."""
        if self._after:
            try:
                self.after_cancel(self._after)
            except Exception:
                pass
            self._after = self.after(int(self.speed_ms.get()), self.tick)

    def _cancel_timer(self) -> None:
        """Cancel any pending execution timer."""
        if self._after:
            self.after_cancel(self._after)
            self._after = None

    def _build_input_bar(self) -> None:
        """Create the input bar for handling Befunge input operations.

        The bar is shown when the interpreter encounters '&' (integer input)
        or '~' (character input) and hidden otherwise.
        """
        bar = ttk.Frame(self)
        lbl = ttk.Label(bar, text="Input:")
        ent = ttk.Entry(bar, width=18)
        btn_send = ttk.Button(bar, text="Send", command=self.send_input)
        btn_cancel = ttk.Button(bar, text="Cancel", command=self._hide_input_bar)

        lbl.pack(side="left")
        ent.pack(side="left", padx=(6,6))
        btn_send.pack(side="left")
        btn_cancel.pack(side="left", padx=(6,0))

        # Store references.
        self.input_bar = bar
        self.input_label = lbl
        self.input_entry = ent

        # Keyboard shortcuts for input.
        ent.bind("<Return>", lambda e: self.send_input())
        ent.bind("<Escape>", lambda e: self._hide_input_bar())

        # Start hidden.
        self.input_bar.pack_forget()

    def _show_input_bar(self) -> None:
        """Display the input bar and focus the entry field.

        Shows the appropriate prompt based on the expected input type (int for
        '&', char for '~') and focuses the entry for typing.
        """
        kind = getattr(self.interp.ip, "waiting_for", None) # WaitTypes.INT or WaitTypes.CHAR
        if not isinstance(kind, WaitTypes):
            return
    
        self.input_label.config(text=f"Input ({kind.value}):")
        self.input_entry.delete(0, tk.END)

        self.input_bar.pack(fill="x", padx=8, pady=(4,8))

        self.input_entry.focus_set()
        self.input_entry.select_range(0, tk.END)

    def _hide_input_bar(self) -> None:
        """Hide the input bar."""
        if getattr(self, "input_bar", None):
            self.input_bar.pack_forget()

    def send_input(self) -> None:
        """Validate user input and send it to the interpreter.

        Validates the input based on the expected type (integer or character),
        sends it to the interpreter, hides the input bar, and resumes execution.
        Provides audio feedback for invalid numeric input.
        """
        kind = getattr(self.interp.ip, "waiting_for", None)
        s = self.input_entry.get()

        if kind is WaitTypes.INT:
            try:
                val = int(s.strip())
            except Exception:
                self.bell()
                return
        elif kind is WaitTypes.CHAR:
            ch = s[0] if s else "\n"
            val = ord(ch)
        else:
            return

        self.interp.provide_input(val)
        self._hide_input_bar()
        self.tick()

    def render(self) -> None:
        """Update the visual display of the grid and interpreter state.

        Refreshes the grid if it changed, highlights the IP position, repaints
        breakpoints, updates the status bar, and refreshes the stack view.
        """
        grid = self.interp.ip.grid
        ip = self.interp.ip

        # Update main window with current grid if grid has changed.
        if self._last_grid_rev != self.interp.grid_rev:
            self.text.configure(state=tk.NORMAL)
            self.text.delete("1.0", tk.END)
            for _, row in enumerate(grid):
                self.text.insert(tk.END, "".join(row) + "\n")
            self.text.configure(state=tk.DISABLED)

            self._last_grid_rev = self.interp.grid_rev
            self._last_ip_xy = None

        if self._last_ip_xy is not None:
            px, py = self._last_ip_xy
            self.text.tag_remove("ip", f"{py+1}.{px}", f"{py+1}.{px+1}")
        self.text.tag_add("ip", f"{ip.y+1}.{ip.x}", f"{ip.y+1}.{ip.x+1}")
        self._last_ip_xy = (ip.x, ip.y)

        # Update breakpoint highlights.
        self._paint_breakpoints()

        # Update status bar with current interpreter state.
        random_indicator = "[RANDOM]" if ip.last_was_random else ""
        self.status.config(
            text=f"IP=({ip.x},{ip.y}) [{ip.direction.glyph}] {random_indicator}   "
            f"Stack size={len(self.interp.stack)}"
            )

        # Update stack visualization.
        self._refresh_stack_view()

    def _sidecar_path(self, program_path: str) -> str:
        """Return the path for the settings sidecar file for a program path."""
        return program_path + ".befmeta.json"
    
    def _current_settings(self) -> Dict[str, Any]:
        """Return current settings as a dict for saving."""
        bps = [{"x": x, "y": y} for (x, y) in sorted(self.breakpoints)]
        return {
            "delay_ms": int(self.speed_ms.get()),
            "steps_per_tick": int(self.steps_per_tick.get()),
            "breakpoints": bps,
        }
    
    def _save_sidecar_settings_if_changed(self) -> None:
        """Save settings to sidecar file if they have changed."""
        if not self.current_path or not self._settings_changed:
            return
        self._save_sidecar_settings()

    def _on_settings_change(self, *_: object) -> None:
        """Handle settings changes for auto-save tracking."""
        if self._suspend_setting_traces:
            return
        self._settings_changed = (self._current_settings() != self._last_saved_settings)
    
    def _load_sidecar_settings(self, program_path: str) -> None:
        """Load settings from the sidecar file associated with a program.

        Attempts to load execution settings and breakpoints from a JSON file stored
        alongside the program. Handles missing or corrupted files gracefully.

        Args:
          program_path: Path to the Befunge program file.
        """
        try:
            with open(self._sidecar_path(program_path), "r", encoding="utf-8") as f:
                meta = json.load(f)
        except FileNotFoundError:
            meta = {}
        except Exception:
            meta = {}   # Corrupted JSON → start fresh
        
        delay   = meta.get("delay_ms")
        steps   = meta.get("steps_per_tick")
        bps     = meta.get("breakpoints", [])

        # Apply settings with validation; temporarily disable change tracking.
        self._suspend_setting_traces = True
        try:
            if isinstance(delay, int) and delay > 0 and delay <= 500:
                self.speed_ms.set(delay)
            if isinstance(steps, int) and steps > 0 and steps <= 50:
                self.steps_per_tick.set(steps)
        finally:
            self._suspend_setting_traces = False

        # Load breakpoints with validation.
        self.breakpoints.clear()
        if isinstance(bps, list):
            for bp in bps:
                if isinstance(bp, dict) and "x" in bp and "y" in bp:
                    self.breakpoints.add((int(bp["x"]), int(bp["y"])))

        self._last_saved_settings = self._current_settings()

    def _save_sidecar_settings(self) -> None:
        """Save current settings to a sidecar JSON file (atomically)."""
        if not self.current_path:
            return
        
        meta = {
            "version":  SETTINGS_VERSION,
            **self._current_settings(),
        }

        sidecar = self._sidecar_path(self.current_path)
        dir_ = os.path.dirname(sidecar) or "."

        try:
            # Atomic write using temporary file.
            fd, tmp = tempfile.mkstemp(prefix=".befmeta.", dir=dir_, text=True)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
                os.replace(tmp, sidecar)
            finally:
                # Clean up temp file if an error occurred before replace.
                if os.path.exists(tmp) and not os.path.samefile(tmp, sidecar):
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
        except Exception:
            # Silently ignore save errors (non-fatal for the app)
            pass

        self._last_saved_settings = self._current_settings()
        self._settings_changed = False

    def _index_to_xy(self, index: str) -> tuple[int, int]:
        """Convert a Tk text index ('line.column') to grid coordinates (x, y)."""
        line, col = index.split(".")
        y = int(line) - 1
        x = int(col)
        return x, y
    
    def _xy_to_index(self, x: int, y: int) -> tuple[str, str]:
        """Convert grid coordinates to Tk text index range (start, end)."""
        start = f"{y+1}.{x}"
        end = f"{y+1}.{x+1}"
        return start, end
    
    def _on_toggle_bp_click(self, e) -> None:
        """Handle Ctrl+LMB to toggle breakpoints at the clicked cell."""
        # Get character at click position.
        idx = self.text.index(f"@{e.x},{e.y}")
        ch = self.text.get(idx, f"{idx}+1c")

        # Ignore clicks on newline.
        if ch == "\n":
            return
        
        x, y = self._index_to_xy(idx)
        if x >= self.interp.ip.orig_width or y >= self.interp.ip.orig_height:
            return
        self._toggle_breakpoint(x, y)

    def _toggle_breakpoint(self, x: int, y: int) -> None:
        """Toggle a breakpoint at (x, y) and update the display."""
        key = (x, y)
        if key in self.breakpoints:
            self.breakpoints.remove(key)
        else:
            self.breakpoints.add(key)
        
        self._on_settings_change()
        self._paint_breakpoints()

    def _paint_breakpoints(self) -> None:
        """Highlight all breakpoints in the text widget (IP takes precedence)."""
        # Clear existing BP tags.
        self.text.tag_remove("bp", "1.0", tk.END)

        # Add tags for all current breakpoints.
        for (x, y) in self.breakpoints:
            start, end = self._xy_to_index(x, y)
            self.text.tag_add("bp", start, end)

        # Ensure IP shows above BPs.
        self.text.tag_raise("ip")

    def _prefill_output_from_interpreter(self) -> None:
        """Initialize output window with current interpreter output."""
        if not (self._out_win and self._out_txt and self._out_win.winfo_exists()):
            return
        
        self._out_txt.configure(state=tk.NORMAL)
        self._out_txt.delete("1.0", tk.END)

        if self.interp.output:
            self._out_txt.insert(tk.END, self.interp.output)
        
        self._out_txt.configure(state=tk.DISABLED)

        # Mark what's been shown-only append deltas later.
        self._out_len = len(self.interp.output)

    def _on_app_close(self) -> None:
        """Handle cleanup when the application is closing (graceful shutdown)."""
        if getattr(self, "_closing", False):
            return # Prevent recursive close handling
        self._closing = True

        # Stop execution timers.
        try:
            self._cancel_timer()
        except Exception:
            pass

        # Dispose tooltip system.
        try:
            if hasattr(self, "_hover") and self._hover:
                self._hover.dispose()
        except Exception:
            pass

        # Close output window.
        try:
            if self._out_win and self._out_win.winfo_exists():
                self._out_win.destroy()
        except Exception:
            pass

        # Save settings if changed.
        try:
            self._save_sidecar_settings_if_changed()
        except Exception:
            pass

        # Destroy main window.
        try:
            self.winfo_toplevel().destroy()
        except Exception:
            pass