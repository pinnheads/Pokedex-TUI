from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer, Header


class PokedexApp(App):
    """A textual app to browse Pokemon stats, with search and filters by name, type and generation"""

    #    CSS_PATH = "pokedex.tcss"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("d", "toggle_dark", "Toggle dark mode"),
        Binding("q", "quit", "Quit app"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app"""
        yield Header(show_clock=True)
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = PokedexApp()
    app.run()
