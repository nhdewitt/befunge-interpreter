"""Interactive opcode hover tooltip system.

Displays contextual opcode documentation when the user hovers over characters
in a Tkinter Text-based Befunge editor. Provides real-time feedback with
cell highlighting and delayed, positioned tooltips.

Key features:
  - Delayed tooltip display to avoid flicker during mouse movement.
  - Visual cell highlighting.
  - Dynamic tooltip positioning that follows the cursor.
  - Monospaced tooltip styling for aligned tables.
  - Automatic cleanup and resource management.
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Optional, Final

TOOLTIP_X_OFFSET: Final[int] = 14
"""Horizontal offset from the mouse pointer in screen pixels."""

TOOLTIP_Y_OFFSET: Final[int] = 16
"""Vertical offset from the mouse pointer in screen pixels."""

class OpcodeHoverTip:
    """Interactive tooltips for displaying opcode documentation on hover.

    Manages hover-based tooltips that appear when the mouse lingers over
    characters in a Text widget. Highlights the hovered cell and displays
    formatted documentation after a configurable delay.

    Attributes:
      text: The Text widget to monitor for hover events.
      formatter: Function that maps a single character to tooltip text.
      delay: Delay in milliseconds before showing a tooltip.
      interp: Optional interpreter instance used by formatters that need state.
      cell_filter: Optional predicate `(ch, x, y) -> bool`; if it returns False,
        the tooltip is suppressed (e.g., outside the original playfield).
      tip: The current tooltip window, or None if not shown.
      after_id: Tk timer ID for the delayed tooltip display, if scheduled.
      last_index: Last text index seen (used to avoid redundant work).
    """
    def __init__(
            self,
            text: tk.Text,
            formatter: Callable[[str], str],delay: int = 250,
            interp=None,
            *,
            cell_filter: Optional[Callable[[str, int, int], bool]]
        ) -> None:
        """Initialize the hover tooltip system.

        Args:
          text: Text widget to attach hover tooltips to.
          formatter: Function that takes a character and returns tooltip content.
          delay: Time in milliseconds to wait before showing a tooltip.
          interp: Optional interpreter (for formatters that depend on state).
          cell_filter: Optional predicate to filter cells (ch, x, y).
        """
        self.text = text
        self.formatter = formatter
        self.delay = delay
        self.interp = interp
        self.cell_filter = cell_filter

        self._fixed_font = tkfont.nametofont("TkFixedFont").copy()
        self._fixed_font.configure(size=10)

        # Tooltip state management.
        self.tip: Optional[tk.Toplevel] = None
        self._tip_lbl: Optional[tk.Label] = None
        self.after_id: Optional[str] = None
        self.last_index: Optional[str] = None
        self._prev_index: Optional[str] = None
        
        # Visual highlighting for hovered cell.
        self.text.tag_configure(
            "hover_cell",
            background="#0a2516",
            foreground="#4ed05d"
        )

        # Bind event handlers (preserve existing bindings with add=True).
        self._bind_ids = {
            "motion": text.bind("<Motion>", self._on_motion, add=True),
            "leave": text.bind("<Leave>", self._on_leave, add=True),
            "press": text.bind("<ButtonPress>", self._on_leave, add=True),
        }

    def _on_motion(self, e: tk.Event) -> None:
        """Handle mouse movement over the text widget.

        Tracks mouse position, updates cell highlighting, and schedules tooltip
        display with the configured delay. Skips redundant work when hovering
        over the same character.

        Args:
          e: Mouse motion event containing x/y coordinates.
        """
        # Convert mouse coordinates to text index.
        idx = self.text.index(f"@{e.x},{e.y}")

        # Skip processing if we're on the same character.
        if idx == self.last_index:
            # Only updating the tooltip position (if visible).
            if self.tip and self.tip.winfo_exists():
                self._move_tip(
                    e.x_root + TOOLTIP_X_OFFSET,
                    e.y_root + TOOLTIP_Y_OFFSET
                )
            return
        
        self.last_index = idx

        # Update visual highlighting.
        if self._prev_index:
            self.text.tag_remove(
                "hover_cell",
                self._prev_index,
                f"{self._prev_index}+1c"
            )
        self.text.tag_add("hover_cell", idx, f"{idx}+1c")
        self.text.tag_raise("hover_cell")
        self._prev_index = idx

        # Cancel any pending tooltip display.
        if self.after_id:
            self.text.after_cancel(self.after_id)
        
        # Schedule new tooltip after delay.
        self.after_id = self.text.after(
            self.delay,
            lambda ix=idx, xr=e.x_root, yr=e.y_root: self._show_for_index(
                ix,
                xr + TOOLTIP_X_OFFSET,
                yr + TOOLTIP_Y_OFFSET
            )
        )
        
    def _on_leave(self, _e: Optional[tk.Event] = None) -> None:
        """Handle mouse leave or button-press events.

        Cancels any pending tooltip display, clears cell highlighting, and hides
        any visible tooltip.

        Args:
          _e: Event object (unused).
        """
        # Cancel delayed tooltip display.
        if self.after_id:
            self.text.after_cancel(self.after_id)
            self.after_id = None

        # Remove visual highlighting.
        self.text.tag_remove("hover_cell", "1.0", tk.END)

        # Hide any visible tooltip.
        self._hide_tip()
    
    def _show_for_index(self, idx: str, x_root: int, y_root: int) -> None:
        """Display a tooltip for the character at the given text index.

        Extracts the character at the index, formats it using the provided
        formatter function, and displays the tooltip. Newlines and empty cells
        suppress the tooltip.

        Args:
          idx: Text widget index in "line.column" format.
          x_root: Screen x-coordinate for tooltip positioning.
          y_root: Screen y-coordinate for tooltip positioning.
        """
        # Get character at specified index.
        ch = self.text.get(idx, f"{idx}+1c")

        # Parse grid coordinates from index.
        line, col = idx.split(".")
        y = int(line) - 1
        x = int(col)

        # Check if position is outside the original playfield.
        if self.cell_filter and not self.cell_filter(ch, x, y):
            self._hide_tip()
            return

        # Don't show tooltips for newlines or empty content.
        if not ch or ch == "\n":
            self._hide_tip()
            return
        
        # Format tooltip content and display.
        self._show_tip(self.formatter(ch), x_root, y_root)

    def _show_tip(self, text: str, x: int, y: int) -> None:
        """Create or update the tooltip window with the specified content.

        Creates a new tooltip window if none exists; otherwise updates the
        existing one.

        Args:
          text: Tooltip content.
          x: Screen x-coordinate for positioning.
          y: Screen y-coordinate for positioning.
        """
        # Update existing tooltip if it exists.
        if self.tip and self.tip.winfo_exists():
            self._update_tip(text)
            self._move_tip(x, y)
            return
        
        # Create new tooltip window.
        tip = tk.Toplevel(self.text)
        tip.overrideredirect(True)  # Remove window decorations
        tip.attributes("-alpha", 0.90)  # Slight transparency

        lbl = tk.Label(
            tip,
            text=text,
            font=self._fixed_font,
            background="#0a2516",
            foreground="#4ed05d",
            relief=tk.RIDGE,
            borderwidth=2,
            justify="left"
        )
        lbl.pack(ipadx=6, ipady=4)

        # Store references.
        self.tip = tip
        self._tip_lbl = lbl

        # Position the tooltip.
        self._move_tip(x, y)

    def _update_tip(self, text: str) -> None:
        """Update the content of the current tooltip, if it changed.

        Args:
          text: New content for the tooltip.
        """
        if self.tip and self.tip.winfo_exists() and self._tip_lbl:
            if self._tip_lbl.cget("text") != text:
                self._tip_lbl.configure(text=text)

    def _move_tip(self, x: int, y: int) -> None:
        """Reposition the tooltip to the specified screen coordinates.

        Keeps the tooltip fully visible on-screen.

        Args:
          x: Screen x-coordinate.
          y: Screen y-coordinate.
        """
        if self.tip and self.tip.winfo_exists():
            sw, sh = self.text.winfo_screenwidth(), self.text.winfo_screenheight()
            self.tip.update_idletasks()
            tw, th = self.tip.winfo_reqwidth(), self.tip.winfo_reqheight()
            x = max(0, min(x, sw - tw))
            y = max(0, min(y, sh - th))
            self.tip.geometry(f"+{x}+{y}")

    def _hide_tip(self) -> None:
        """Hide and destroy the current tooltip window (if any)."""
        if self.tip and self.tip.winfo_exists():
            self.tip.destroy()
        self.tip = None
        self._tip_lbl = None

    def dispose(self) -> None:
        """Clean up all tooltip resources and cancel pending operations.

        Call this when the tooltip system is no longer needed (e.g., app
        shutdown). Ensures timers are cancelled and windows are destroyed.
        """
        # Cancel any pending delayed tooltip display.
        if self.after_id:
            try:
                self.text.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
        
        # Hide and destroy any visible tooltip.
        self._hide_tip()

        # Unbind event handlers.
        try:
            self.text.unbind("<Motion>", self._bind_ids.get("motion"))
            self.text.unbind("<Leave>", self._bind_ids.get("leave"))
            self.text.unbind("<ButtonPress>", self._bind_ids.get("press"))
        except Exception:
            pass