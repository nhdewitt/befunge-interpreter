# from datetime import datetime

# from textual.app import App, ComposeResult
# from textual.widgets import Footer, Header


# class BefungeVisualizer(App):

#     BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

#     def compose(self) -> ComposeResult:
#         """Create child widgets for the app."""
#         yield Header(name="Befunge Visualizer", show_clock=True, icon='A')
#         yield Footer()

#     def action_toggle_dark(self) -> None:
#         """An action to toggle dark mode."""
#         self.theme = {
#             "textual-dark" if self.theme == "textual-light" else "textual-light"
#         }

# app = BefungeVisualizer()
# app.run()