from textual.app import App, ComposeResult
from textual.containers import Container
from textual.binding import Binding
from textual.widgets import Static

class BefungeOutput(Static):
    """Custom widget for displaying Befunge output"""
    
    DEFAULT_CSS = """
    BefungeOutput {
        display: block;
        width: 60;
        height: 20;
        background: #2d2d2d;
        color: lime;
        border: solid lime;
        padding: 1;
        content-align: left middle;
    }
    """

class BefungeApp(App):
    """Main Befunge interpreter application"""
    
    CSS = """
    Screen {
        background: #000000;
    }

    Container {
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit")
    ]

    def __init__(self, interpret_fn, code):
        super().__init__()
        self.interpret_fn = interpret_fn
        self.code = code
        self.output = ""

    def compose(self) -> ComposeResult:
        with Container():
            yield BefungeOutput("Starting...", id="display")

    async def on_mount(self) -> None:
        self.display = self.query_one(BefungeOutput)
        gen = self.interpret_fn(self.code)
        
        while True:
            try:
                output = next(gen)
                if output:
                    self.output += str(output)
                    self.display.update(self.output)
            except StopIteration:
                self.display.update(self.output + "\n[Done]")
                break