import argparse
import tkinter as tk
from tkinter import messagebox
from ui.app import App
from core.interpreter import Interpreter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", help="Befunge source file to open")
    args = parser.parse_args()

    root = tk.Tk()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                src = f.read()
        except Exception as e:
            messagebox.showerror("Open failed", f"Could not open '{args.file}':\n{e}", parent=root)
            src = ""
            open_on_start = True
        else:
            open_on_start = False

        interp = Interpreter(src)
        app = App(root, interp, open_on_start=open_on_start)
        app.pack(fill="both", expand=True)

        if not open_on_start:
            app.load_file(src, args.file)
    else:
        interp = Interpreter("")
        app = App(root, interp, open_on_start=True)
        app.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()