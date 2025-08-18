import argparse
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Optional

from ui.app import App
from core.interpreter import Interpreter
from validate.validate_load import is_befunge_path, possibly_valid_befunge

def launch_app(root: tk.Tk, src: str, path: Optional[str], open_on_start: bool) -> None:
    interp = Interpreter(src)
    app = App(root, interp, open_on_start=open_on_start)
    app.pack(fill=tk.BOTH, expand=True)
    if path and not open_on_start:
        app.load_file(src, path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", help="Befunge source file to open")
    args = parser.parse_args()

    root = tk.Tk()

    src = ""
    open_on_start = True
    path = args.file

    if path:
        if not is_befunge_path(path):
            messagebox.showerror(
                "Not a befunge file",
                "Please choose a .bf or .befunge file.",
                parent=root,
            )
        else:
            try:
                with open(path, 'r', encoding="utf-8") as f:
                    src = f.read()
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
                        "Not Befunge file",
                        "The file does not appear to be valid Befunge-93 source code.",
                        parent=root,
                    )

    launch_app(root, src, path if not open_on_start else None, open_on_start)
    root.mainloop()

if __name__ == "__main__":
    main()