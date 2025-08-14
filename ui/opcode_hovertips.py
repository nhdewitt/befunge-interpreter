import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

class OpcodeHoverTip:
    def __init__(self, text: tk.Text,
                 formatter: Callable[[str], str],
                 delay: int = 250):
        self.text = text
        self.formatter = formatter
        self.delay = delay
        self.tip: tk.Toplevel | None = None
        self._tip_lbl: tk.Label | None = None
        self.after_id: str | None = None
        self.last_index: str | None = None
        
        self.text.tag_configure("hover_cell", background="#ffe08a")

        text.bind("<Motion>", self._on_motion, add=True)
        text.bind("<Leave>", self._on_leave, add=True)
        text.bind("<ButtonPress>", self._on_leave, add=True)

    def _on_motion(self, e: tk.Event):
        idx = self.text.index(f"@{e.x},{e.y}")
        if idx == self.last_index:
            if self.tip and self.tip.winfo_exists():
                self._move_tip(e.x_root + 14, e.y_root + 16)
            return
        self.last_index = idx

        self.text.tag_remove("hover_cell", "1.0", "end")
        self.text.tag_add("hover_cell", idx, f"{idx}+1c")

        if self.after_id:
            self.text.after_cancel(self.after_id)
        self.after_id = self.text.after(self.delay,
                                        lambda ix=idx, xr=e.x_root, yr=e.y_root:
                                        self._show_for_index(ix, xr + 14, yr + 16))
        
    def _on_leave(self, _e=None):
        if self.after_id:
            self.text.after_cancel(self.after_id)
            self.after_id = None
        self.text.tag_remove("hover_cell", "1.0", "end")
        self._hide_tip()
    
    def _show_for_index(self, idx: str, x_root: int, y_root: int):
        ch = self.text.get(idx, f"{idx}+1c")
        if ch == "\n" or ch == "":
            self._hide_tip()
            return
        text = self.formatter(ch)
        self._show_tip(text, x_root, y_root)

    def _show_tip(self, text: str, x: int, y: int):
        if self.tip and self.tip.winfo_exists():
            self._update_tip(text)
            self._move_tip(x, y)
            return
        
        tip = tk.Toplevel(self.text)
        tip.overrideredirect(True)
        tip.attributes("-alpha", 0.98)

        fixed = tkfont.nametofont("TkFixedFont").copy()
        fixed.configure(size=10)

        lbl = tk.Label(
            tip,
            text=text,
            font=fixed,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            justify="left"
        )
        lbl.pack(ipadx=6, ipady=4)
        self.tip = tip
        self._tip_lbl = lbl
        self._move_tip(x, y)

    def _update_tip(self, text: str):
        if self.tip and self.tip.winfo_exists() and self._tip_lbl:
            if self._tip_lbl.cget("text") != text:
                self._tip_lbl.configure(text=text)

    def _move_tip(self, x: int, y: int):
        if self.tip and self.tip.winfo_exists():
            self.tip.geometry(f"+{x}+{y}")

    def _hide_tip(self):
        if self.tip and self.tip.winfo_exists():
            self.tip.destroy()
        self.tip = None

    def dispose(self):
        """cancel delayed show"""
        if self.after_id:
            try:
                self.text.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
        
        # hide any live windows
        self._hide_tip()