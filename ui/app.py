import json, os, tempfile
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from core.interpreter import Interpreter, StepStatus
from ui.opcode_hovertips import OpcodeHoverTip
from ui.opcodes import OPCODES, format_tooltip_for_opcode, compute_widths
from ui.format_stack import fmt_stack_item

COL_WIDTHS = compute_widths(OPCODES)

SETTINGS_VERSION = 1
DEFAULT_SETTINGS = {
    "version":      SETTINGS_VERSION,
    "delay_ms":         50,
    "steps_per_tick":   1,
}

def tooltip_formatter(ch: str) -> str:
    if ch.isdigit():
        return format_tooltip_for_opcode(ch,
                                         rows={ch: ("(push digit)", "", ch)},
                                         widths=COL_WIDTHS)
    if ch == " ":
        return format_tooltip_for_opcode(ch,
                                         rows={ch: ("(noop)", "", "(no effect)")},
                                         widths=COL_WIDTHS)
    
    return format_tooltip_for_opcode(ch, rows=OPCODES, widths=COL_WIDTHS)

class App(ttk.Frame):
    def __init__(self, master: tk.Misc, interp: Interpreter, *, open_on_start: bool = True, **kwargs):
        super().__init__(master, **kwargs)
        root = self.winfo_toplevel()
        root.protocol("WM_DELETE_WINDOW", self._on_app_close)

        self.interp = interp
        self._after = None
        self._shown_output = False

        self._out_win: tk.Toplevel | None = None
        self._out_txt: tk.Text | None = None
        self._out_len: int = 0
        self._out_autoscroll = tk.BooleanVar(value=True)

        self._stack_lb: tk.Listbox | None = None

        self.speed_ms = tk.IntVar(value=DEFAULT_SETTINGS["delay_ms"])                   # delay between ticks (ms)
        self.steps_per_tick = tk.IntVar(value=DEFAULT_SETTINGS["steps_per_tick"])       # number of steps per tick

        self._last_saved_settings: dict[str, int] = {
            "delay_ms":         int(self.speed_ms.get()),
            "steps_per_tick":   int(self.steps_per_tick.get()),
        }
        self._settings_changed = False
        self._suspend_setting_traces = False
        self.speed_ms.trace_add("write", self._on_settings_change)
        self.steps_per_tick.trace_add("write", self._on_settings_change)

        self.current_path: str | None = None
        self.last_dir: str | None = None

        self._build()
        self._build_input_bar()
        self._bind()

        if open_on_start:
            self.after_idle(self.open_file)

        self.after_idle(self.render)    # display code after loading and before running/stepping

    def open_file(self):
        """Prompt user to open a Befunge source file - default directory is ./src"""
        initial_dir = os.path.expanduser("./src")
        path = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            initialdir=initial_dir,
            title="Load Befunge file",
            filetypes=[("Befunge (*.bf, *.befunge)", "*.bf *.befunge"), ("All files (*.*)", "*.*")]
        )
        if not path:
            return
        
        # if we're switching from another file, save settings for old file first
        self._save_sidecar_settings_if_changed()

        try:
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()
        except Exception as e:
            messagebox.showerror(f"Failed to open {path}", f"Could not open file:\n{e}", parent=self.winfo_toplevel())
            return
        
        self.current_path = path
        self._load_sidecar_settings(path)
        self.load_file(src, path)
        
    def load_file(self, src: str, path: str | None = None):
        """Stop currently running program (if any), load code, clear output, and render."""
        self.stop()
        self.interp.load(src)
        self._clear_output_text()
        self.render()

        self.current_path = path
        if path:
            self.last_dir = os.path.dirname(path)
        self._set_title()

    def _set_title(self):
        """Display current file name in window title."""
        root = self.winfo_toplevel()
        name = os.path.basename(self.current_path) if self.current_path else "(untitled)"
        root.title(f"Befunge - {name}")

    def open_output_window(self, clear: bool = True):
        """Displays output string as separate window"""
        if self._out_win and self._out_win.winfo_exists():
            self._out_win.deiconify()
            self._out_win.lift()
            if clear:
                self._clear_output_text()
                self._refresh_stack_view()
                self._prefill_output_from_interpreter()
            return
        
        win = tk.Toplevel(self)
        win.title("Program Output")
        win.resizable(True, True)
        win.transient(self.winfo_toplevel())

        content = ttk.Frame(win)
        content.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        pw = ttk.Panedwindow(content, orient=tk.HORIZONTAL)
        pw.pack(fill="both", expand=True)

        # LHS: output text and scrollbar
        left = ttk.Frame(pw)
        txt = tk.Text(left, wrap=tk.WORD, font=("Consolas", 11), height=16)
        yscroll_out = ttk.Scrollbar(left, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(state=tk.DISABLED, yscrollcommand=yscroll_out.set)

        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        txt.grid(row=0, column=0, sticky=tk.NSEW)
        yscroll_out.grid(row=0, column=1, sticky=tk.NS)

        # RHS: stack Listbox (top -> bottom) and scrollbar
        right = ttk.Frame(pw, width=160)
        ttk.Label(right, text="Stack").pack(anchor=tk.W, padx=4, pady=(0, 4))
        lb = tk.Listbox(right, font=("Consolas", 11), activestyle=tk.NONE)
        yscroll_stack = ttk.Scrollbar(right, orient=tk.VERTICAL, command=lb.yview)
        lb.configure(yscrollcommand=yscroll_stack.set)

        lb.pack(side=tk.LEFT, fill="both", expand=True, padx=(4, 0), pady=(0, 4))
        yscroll_stack.pack(side=tk.LEFT, fill="y", padx=(0, 4), pady=(0, 4))

        pw.add(left, weight=4)
        pw.add(right, weight=1)

        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=(6, 8))

        ttk.Checkbutton(bar, text="Autoscroll", variable=self._out_autoscroll).pack(side=tk.LEFT)

        def copy_all():
            self.clipboard_clear()
            self.clipboard_append(self.interp.output)
        
        def save_to_file():
            path = filedialog.asksaveasfilename(
                parent=win, title="Save output",
                defaultextension=".txt",
                filetypes=[("Text files (*.txt)", "*.txt"), ("All files (*.*)", "*.*")]
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.interp.output)
        
        ttk.Button(bar, text="Copy", command=copy_all).pack(side=tk.LEFT, padx=(8,0))
        ttk.Button(bar, text="Save...", command=save_to_file).pack(side=tk.LEFT, padx=6)
        ttk.Button(bar, text="Clear", command=self._clear_output_text).pack(side=tk.LEFT, padx=6)
        ttk.Button(bar, text="Close", command=win.destroy).pack(side=tk.RIGHT)

        self._out_win = win
        self._out_txt = txt
        self._stack_lb = lb
        self._out_len = 0

        if clear:
            self._clear_output_text()
            self._prefill_output_from_interpreter()
        else:
            self._out_len = len(self.interp.output)

        def on_close():
            self._out_win = None
            self._out_txt = None
            self._stack_lb = None
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_close)

        win.update_idletasks()
        win.geometry(f"+{self.winfo_rootx()+40}+{self.winfo_rooty()+40}")

        if clear:
            self._clear_output_text()
        self._refresh_stack_view()

    def _refresh_stack_view(self):
        """Render the stack into the right-hand listbox."""
        if not (self._out_win and self._stack_lb and self._out_win.winfo_exists()):
            return
        lb = self._stack_lb
        lb.delete(0, tk.END)

        items = list(self.interp.stack)
        for v in reversed(items):
            lb.insert(tk.END, fmt_stack_item(v))

    def _clear_output_text(self):
        self._out_len = 0
        if self._out_txt and self._out_txt.winfo_exists():
            self._out_txt.configure(state="normal")
            self._out_txt.delete("1.0", "end")
            self._out_txt.configure(state="disabled")

    def _append_output_if_needed(self):
        """Append only new txt from interp.output into the live window."""
        if not (self._out_win and self._out_txt and self._out_win.winfo_exists()):
            return
        out = self.interp.output
        if len(out) == self._out_len:
            return
        new_chunk = out[self._out_len:]
        self._out_len = len(out)

        self._out_txt.configure(state="normal")
        self._out_txt.insert(tk.END, new_chunk)
        self._out_txt.configure(state="disabled")
        if self._out_autoscroll.get():
            self._out_txt.see(tk.END)
        self._refresh_stack_view()

    def _build(self):
        toolbar = ttk.Frame(self)
        self.btn_open = ttk.Button(toolbar, text="Open... (Ctrl-O)", command=self.open_file)
        self.btn_run = ttk.Button(toolbar, text="Run (F5)", command=lambda: self.run(resume=True, clear_output=True))
        self.btn_step = ttk.Button(toolbar, text="Step (F10)", command=self.step_once)
        self.btn_stop = ttk.Button(toolbar, text="Stop (Esc)", command=self.stop)
        for w in (self.btn_open, self.btn_run, self.btn_step, self.btn_stop):
            w.pack(side=tk.LEFT, padx=4)
        toolbar.pack(fill=tk.X, pady=4)

        ttk.Label(toolbar, text="Delay (ms)").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Scale(toolbar, from_=1, to=500, variable=self.speed_ms,
                  orient=tk.HORIZONTAL, length=120).pack(side=tk.LEFT)
        
        ttk.Label(toolbar, text="Steps/tick").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Scale(toolbar, from_=1, to=1000, variable=self.steps_per_tick,
                  orient=tk.HORIZONTAL, length=140).pack(side=tk.LEFT)

        self.text = tk.Text(self, width=80, height=25, font=("Consolas", 12))
        self.text.configure(state="disabled")
        self.text.pack(fill=tk.BOTH, expand=True)

        self._hover = OpcodeHoverTip(self.text, formatter=tooltip_formatter, delay=250)        

        self.status = ttk.Label(self, anchor="w")
        self.status.pack(fill=tk.X)

    def _bind(self):
        self.master.bind("<Control-o>", lambda e: self.open_file())
        self.master.bind("<F5>", lambda e: self.run())
        self.master.bind("<F10>", lambda e: self.step_once())
        self.master.bind("<Escape>", lambda e: self.stop())

    def run(self, interval_ms: int | None = None, *,
            resume: bool = True, clear_output: bool = False):
        self._cancel_timer()
        # If mid-run, don't clear
        self.open_output_window(clear=clear_output)
        # If cleared, prefill output so we're not inserting the whole backlog
        if clear_output:
            self._prefill_output_from_interpreter()
        if interval_ms is None:
            interval_ms = self.speed_ms.get() if hasattr(self, "speed_ms") else 10
        self.tick(interval_ms)

    def step_once(self):
        self._cancel_timer()
        self.render()
        self._append_output_if_needed()
        if StepStatus.AWAITING_INPUT:
            self._show_input_bar()
        elif StepStatus.HALTED:
            pass    # leave the output window open with the final text

    def tick(self, interval=10):
        status = StepStatus.RUNNING
        steps = self.steps_per_tick.get()
        for _ in range(steps):
            status = self.interp.step()
            if status is not StepStatus.RUNNING:
                break

        self.render()
        self._append_output_if_needed()

        if status is StepStatus.RUNNING:
            self._after = self.after(interval, self.tick, interval)
        elif status is StepStatus.AWAITING_INPUT:
            self._show_input_bar()
        else:   # HALTED
            self._cancel_timer()
    
    def stop(self):
        """Cancel loop but keep output window open if user clicks stop"""
        self._cancel_timer()
        if hasattr(self, "input_bar"):
            self.input_bar.pack_forget()

    def _cancel_timer(self):
        if self._after:
            self.after_cancel(self._after)
            self._after = None

    def _build_input_bar(self):
        """Create the input bar but don't show it until code reaches user input."""
        bar = ttk.Frame(self)
        lbl = ttk.Label(bar, text="Input:")
        ent = ttk.Entry(bar, width=18)
        btn_send = ttk.Button(bar, text="Send", command=self.send_input)
        btn_cancel = ttk.Button(bar, text="Cancel", command=self._hide_input_bar)

        lbl.pack(side="left")
        ent.pack(side="left", padx=(6,6))
        btn_send.pack(side="left")
        btn_cancel.pack(side="left", padx=(6,0))

        self.input_bar = bar
        self.input_label = lbl
        self.input_entry = ent

        ent.bind("<Return>", lambda e: self.send_input())
        ent.bind("<Escape>", lambda e: self._hide_input_bar())

        self.input_bar.pack_forget()

    def _show_input_bar(self):
        """Show the bar and get input."""
        kind = getattr(self.interp.ip, "waiting_for", None) # "int" or "char"
        if kind not in ("int", "char"):
            return
        
        self.input_label.config(text=f"Input ({kind}):")
        self.input_entry.delete(0, "end")

        self.input_bar.pack(fill="x", padx=8, pady=(4,8))
        self.input_entry.focus_set()

    def _hide_input_bar(self):
        if getattr(self, "input_bar", None):
            self.input_bar.pack_forget()

    def send_input(self):
        """Read entry, validate, send to interpreter, hide bar, resume processing."""
        kind = getattr(self.interp.ip, "waiting_for", None)
        s = self.input_entry.get()

        if kind == "int":
            try:
                val = int(s.strip())
            except Exception:
                self.bell()
                return
        else:
            ch = s[0] if s else "\n"
            val = ord(ch)

        self.interp.provide_input(val)
        self._hide_input_bar()
        self.tick()

    def render(self):
        grid = self.interp.ip.grid
        ip = self.interp.ip

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        for y, row in enumerate(grid):
            self.text.insert("end", "".join(row) + "\n")
        
        self.text.tag_delete("ip")
        self.text.tag_configure("ip", background="#ffe08a")
        self.text.tag_add("ip", f"{ip.y+1}.{ip.x}", f"{ip.y+1}.{ip.x+1}")
        self.text.configure(state="disabled")

        self.status.config(text=f"IP=({ip.x},{ip.y}) [{ip.direction.glyph}]  Stack size={len(self.interp.stack)}")

        self._refresh_stack_view()

    def _sidecar_path(self, program_path: str) -> str:
        return program_path + ".befmeta.json"
    
    def _current_settings(self) -> dict[str, int]:
        return {
            "delay_ms":         int(self.speed_ms.get()),
            "steps_per_tick":   int(self.steps_per_tick.get()),
        }
    
    def _save_sidecar_settings_if_changed(self):
        if not self.current_path or self._settings_changed:
            return
        self._save_sidecar_settings()

    def _on_settings_change(self, *_):
        if self._suspend_setting_traces:
            return
        self._settings_dirty = (self._current_settings() != self._last_saved_settings)
    
    def _load_sidecar_settings(self, program_path: str):
        """Read JSON and, if present, apply delay/steps to loaded file."""
        try:
            with open(self._sidecar_path(program_path), "r", encoding="utf-8") as f:
                meta = json.load(f)
        except FileNotFoundError:
            meta = {}
        except Exception:
            meta = {}      # TODO: handle corrupted JSON (or just keep ignoring? new changes will overwrite)
        
        delay = meta.get("delay_ms")
        steps = meta.get("steps_per_tick")

        self._suspend_setting_traces = True
        try:
            if isinstance(delay, int) and delay > 0 and delay <= 250:
                self.speed_ms.set(delay)
            if isinstance(steps, int) and steps > 0 and steps <= 1000:
                self.steps_per_tick.set(steps)
        finally:
            self._suspend_setting_traces = False

        self._last_saved_settings = self._current_settings()
        self._settings_dirty = False

    def _save_sidecar_settings(self):
        """Write JSON next to current file."""
        if not self.current_path:
            return
        meta = {
            "version":          SETTINGS_VERSION,
            **self._current_settings(),
        }
        sidecar = self._sidecar_path(self.current_path)
        dir_ = os.path.dirname(sidecar)
        try:
            fd, tmp = tempfile.mkstemp(prefix=".befmeta.", dir=dir_, text=True)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
                os.replace(tmp, sidecar)
            finally:
                if os.path.exists(tmp) and not os.path.samefile(tmp, sidecar):
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
        except Exception:
            pass

        self._last_saved_settings = self._current_settings()
        self._settings_changed = False

    def _prefill_output_from_interpreter(self):
        if not (self._out_win and self._out_txt and self._out_win.winfo_exists()):
            return
        self._out_txt.configure(state=tk.NORMAL)
        self._out_txt.delete("1.0", tk.END)
        if self.interp.output:
            self._out_txt.insert(tk.END, self.interp.output)
        self._out_txt.configure(state=tk.DISABLED)
        # mark what's been shown - only append deltas
        self._out_len = len(self.interp.output)

    def _on_app_close(self):
        """Performed on closing App"""
        if getattr(self, "_closing", False):
            return
        self._closing = True

        # stop timers
        try:
            self._cancel_timer()
        except Exception:
            pass

        # dispose tooltip
        try:
            if hasattr(self, "_hover") and self._hover:
                self._hover.dispose()
        except Exception:
            pass

        # close output toplevel
        try:
            if self._out_win and self._out_win.winfo_exists():
                self._out_win.destroy()
        except Exception:
            pass

        # save settings if changed
        try:
            self._save_sidecar_settings_if_changed()
        except Exception:
            pass

        # destroy root
        try:
            self.winfo_toplevel().destroy()
        except Exception:
            pass