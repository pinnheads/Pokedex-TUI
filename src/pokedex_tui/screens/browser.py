from textual.app import ComposeResult
from textual.containers import HorizontalGroup
from textual.widgets import Button


class Browser(HorizontalGroup):
    """Browser Screen for the main app"""

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch"""
        yield Button("Start", id="start", variant="success")
