"""
Interactive Opcode Hover Tooltip System

Implements a hover tooltip system for the Befunge editor that displays
contextual opcode documentation when the user hovers over characters in
the code grid. The system provides real-time feedback about Befunge
operations.

Key features:
    - Delayed tooltip display to avoid flickering during mouse movement
    - Visual cell highlighting
    - Dynamic tooltip positioning that follows the mouse cursor
    - Tooltip styling with monospaced fonts for aligned tables
    - Automatic cleanup and resource management
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Optional

TOOLTIP_X_OFFSET = 14
TOOLTIP_Y_OFFSET = 16

class OpcodeHoverTip:
    """
    Interactive tooltip system for displaying opcode documentation on hover.

    Manages hover-based tooltips that appear when the mouse lingers over
    characters in a `Text` widget. It provides visual feedback through cell
    highlighting and displays formatted documentation after a configurable
    delay.

    Attributes:
        `text`: The `Text` widget to monitor for hover events
        `formatter`: Function that converts characters to tooltip content
        `delay`: Time to wait (in ms) before showing tooltips
        `tip`: Current tooltip window (`None` if not shown)
        `after_id`: Timer ID for delayed tooltip display
        `last_index`: Last text index to avoid redundant processing
    """
    def __init__(self, text: tk.Text,
                 formatter: Callable[[str], str],
                 delay: int = 250,
                 interp=None,
                 *,
                 cell_filter: Optional[Callable[[str, int, int], bool]]):
        """
        Initialize the hover tooltip system for a `Text` widget.

        Args:
            `text`: `Text` widget to attach hover tooltips to
            `formatter`: Function that takes a character and returns tooltip content
            `delay`: Time in ms to wait before showing tooltip (default 250ms)
        """
        self.text = text
        self.formatter = formatter
        self.delay = delay
        self.interp = interp
        self.cell_filter = cell_filter

        self._fixed_font = tkfont.nametofont("TkFixedFont").copy()
        self._fixed_font.configure(size=10)

        # Tooltip state management
        self.tip: Optional[tk.Toplevel] = None
        self._tip_lbl: Optional[tk.Label] = None
        self.after_id: Optional[str] = None
        self.last_index: Optional[str] = None
        self._prev_index: Optional[str] = None
        
        # Visual highlighting for hovered cell
        self.text.tag_configure("hover_cell", background="#0a2516", foreground="#4ed05d")

        # Bind event handlers (preserve existing bindings with add=True)
        self._bind_ids = {
            "motion": text.bind("<Motion>", self._on_motion, add=True),
            "leave": text.bind("<Leave>", self._on_leave, add=True),
            "press": text.bind("<ButtonPress>", self._on_leave, add=True),
        }

    def _on_motion(self, e: tk.Event) -> None:
        """
        Handle mouse movement over the text widget.

        Tracks mouse position, updates cell highlighting, and schedules
        tooltip display with appropriate delay. Optimizes performance by
        avoiding redundant processing when hovering over the same character.

        Args:
            `e`: Mouse motion event containing `x,y` coordinates
        """
        # Convert mouse coordinates to text index
        idx = self.text.index(f"@{e.x},{e.y}")

        # Skip processing if we're on the same character
        if idx == self.last_index:
            # Only updating the tooltip position
            if self.tip and self.tip.winfo_exists():
                self._move_tip(
                    e.x_root + TOOLTIP_X_OFFSET,
                    e.y_root + TOOLTIP_Y_OFFSET)
            return
        
        self.last_index = idx

        # Update visual highlighting
        if self._prev_index:
            self.text.tag_remove("hover_cell", self._prev_index, f"{self._prev_index}+1c")
        self.text.tag_add("hover_cell", idx, f"{idx}+1c")
        self.text.tag_raise("hover_cell")
        self._prev_index = idx

        # Cancel any pending tooltip display
        if self.after_id:
            self.text.after_cancel(self.after_id)
        
        # Schedule new tooltip after delay
        self.after_id = self.text.after(self.delay,
                                        lambda ix=idx, xr=e.x_root, yr=e.y_root:
                                        self._show_for_index(
                                            ix,
                                            xr + TOOLTIP_X_OFFSET,
                                            yr + TOOLTIP_Y_OFFSET))
        
    def _on_leave(self, _e: Optional[tk.Event] = None) -> None:
        """
        Handle mouse leaving the text widget or button press events.

        Immediately cancels any pending tooltip display, removes visual
        highlighting, and hides any currently shown tooltip. This ensures
        tooltips don't appear after the mouse has left the area.

        Args:
            `_e`: Event object (unused but required for event binding)
        """
        # Cancel delayed tooltip display
        if self.after_id:
            self.text.after_cancel(self.after_id)
            self.after_id = None

        # Remove visual highlighting
        self.text.tag_remove("hover_cell", "1.0", tk.END)

        # Hide any visible tooltip
        self._hide_tip()
    
    def _show_for_index(self, idx: str, x_root: int, y_root: int) -> None:
        """
        Display tooltip for the character at the specified text index.

        Extracts the character at the given index, formats it using the
        provided formatted function, and displays the resulting tooltip.
        Handles newlines and empty content gracefully.

        Args:
            `idx`: `Text` widget index in `line.column` format
            `x_root`: Screen x-coordinate for tooltip positioning
            `y_root`: Screen y-coordinate for tooltip positioning
        """
        # Get character at specified index
        ch = self.text.get(idx, f"{idx}+1c")

        # Parse position from index
        line, col = idx.split(".")
        y = int(line) - 1
        x = int(col)

        # Check if position is outside original playfield
        if self.cell_filter and not self.cell_filter(ch, x, y):
            self._hide_tip()
            return

        # Don't show tooltips for newlines or empty content
        if ch == "\n":
            self._hide_tip()
            return
        
        # Format tooltip content and display
        self._show_tip(self.formatter(ch), x_root, y_root)

    def _show_tip(self, text: str, x: int, y: int) -> None:
        """
        Create or update the tooltip window with the specified content.

        Creates a new tooltip window if none exists, or updates the existing
        one with new content.

        Args:
            `text`: Content to display in the tooltip
            `x`: Screen x-coordinate for positioning
            `y`: Screen y-coordinate for positioning
        """
        # Update existing tooltip if it exists
        if self.tip and self.tip.winfo_exists():
            self._update_tip(text)
            self._move_tip(x, y)
            return
        
        # Create new tooltip window
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

        # Store references for later updates
        self.tip = tip
        self._tip_lbl = lbl

        # Position the tooltip
        self._move_tip(x, y)

    def _update_tip(self, text: str) -> None:
        """
        Update the content of an existing tooltip.

        Changes the text content of the current tooltip if it differs
        from the existing content. Avoids unnecessary updates.

        Args:
            `text`: New content for the tooltip
        """
        if self.tip and self.tip.winfo_exists() and self._tip_lbl:
            if self._tip_lbl.cget("text") != text:
                self._tip_lbl.configure(text=text)

    def _move_tip(self, x: int, y: int) -> None:
        """
        Reposition the tooltip to the specified screen coordinates.

        Updates the tooltip window position to follow mouse movement.
        Coordinates offset from the mouse position to avoid cursor
        interference.

        Args:
            `x`: Screen x-coordinate
            `y`: Screen y-coordinate
        """
        if self.tip and self.tip.winfo_exists():
            sw, sh = self.text.winfo_screenwidth(), self.text.winfo_screenheight()
            self.tip.update_idletasks()
            tw, th = self.tip.winfo_reqwidth(), self.tip.winfo_reqheight()
            x = max(0, min(x, sw - tw))
            y = max(0, min(y, sh - th))
            self.tip.geometry(f"+{x}+{y}")

    def _hide_tip(self) -> None:
        """
        Hide and destroy the current tooltip window.

        Safely destroys the tooltip window and clears internal references.
        Can be called safely even when no tooltip is currently shown.
        """
        if self.tip and self.tip.winfo_exists():
            self.tip.destroy()
        self.tip = None
        self._tip_lbl = None

    def dispose(self) -> None:
        """
        Clean up all tooltip resources and cancel pending operations.

        This method should be called when the tooltip system is no longer
        needed (i.e. at app shutdown). Ensures all timers are cancelled and
        windows are properly destroyed.

        Handles exceptions gracefully to ensure cleanup proceeds even if
        individual steps fail.
        """
        # Cancel any pending delayed tooltip display
        if self.after_id:
            try:
                self.text.after_cancel(self.after_id)
            except Exception:
                pass    # Ignore errors
            self.after_id = None
        
        # Hide and destroy any visible tooltip
        self._hide_tip()

        try:
            self.text.unbind("<Motion>",        self._bind_ids.get("motion"))
            self.text.unbind("<Leave>",         self._bind_ids.get("leave"))
            self.text.unbind("<ButtonPress>",   self._bind_ids.get("press"))
        except Exception:
            pass