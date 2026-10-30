from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static


class StatsPanel(Vertical):
    BORDER_TITLE = "Details"
    DEFAULT_CSS = """
    StatsPanel {
        background: $raised;
        height: auto;
        border: solid $border-blurred;
    }
    """

    def compose(self) -> ComposeResult:
        """Adds this widgets to screen, data is added later"""
        yield Static(classes="name-line")
        yield Static(classes="form-line")
        yield Horizontal(classes="types-container")
        yield Static(classes="stat-rows")
        yield Static(classes="total-row")
        yield Static("enter: full details", classes="hint-line")
