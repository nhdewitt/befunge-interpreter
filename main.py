"""CLI launcher for the Befunge-93 Tkinter GUI."""

import argparse
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from typing import Optional

from ui.app import App
from core.interpreter import Interpreter
from validate.validate_load import is_befunge_path, possibly_valid_befunge

def launch_app(root: tk.Tk, src: str, path: Optional[str], open_on_start: bool) -> None:
    """Create the interpreter + app, pack it, and optionally load a file.

    Args:
      root: Tk root window.
      src: Initial source code (may be empty).
      path: Path to the current file (or None if unsaved).
      open_on_start: If True, show the open dialog on startup.
    """
    interp = Interpreter(src)
    app = App(root, interp, open_on_start=open_on_start)
    app.pack(fill=tk.BOTH, expand=True)
    if path and not open_on_start:
        app.load_file(src, path)

def main():
    """Entry point: parse args, optionally preload a file, launch the GUI."""
    parser = argparse.ArgumentParser(
        prog="befunge-gui",
        description="Befunge-93 GUI with live visualization and debugging."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Befunge source file to open (.bf or .befunge)"
    )
    args = parser.parse_args()

    root = tk.Tk()
    root.withdraw()
    root.title("Befunge")

    # Set window opacity if supported.
    try:
        root.attributes("-alpha", 0.95)
    except Exception:
        pass
    
    src = ""
    open_on_start = True
    path = args.file

    if path:
        p = Path(path)
        if not p.exists():
            messagebox.showerror(
                "File not found",
                f"'{path}' does not exist.",
                parent=root
            )
        elif not is_befunge_path(p):
            messagebox.showerror(
                "Not a befunge file",
                "Please choose a .bf or .befunge file.",
                parent=root
            )
        else:
            try:
                src = p.read_text(encoding="utf-8")
            except Exception as e:
                messagebox.showerror(
                    "Failed to open",
                    f"Could not open '{path}':\n{e}",
                    parent=root,
                )
            else:
                if possibly_valid_befunge(src, require_halt=False):
                    open_on_start = False
                else:
                    messagebox.showerror(
                        "Not Befunge-93 source",
                        "The file does not appear to be valid Befunge-93 source code.",
                        parent=root
                    )

    root.deiconify()
    launch_app(root, src, path if not open_on_start else None, open_on_start)
    root.mainloop()

if __name__ == "__main__":
    main()