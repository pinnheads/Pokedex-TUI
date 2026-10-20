from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer, Header

import pokedex_tui
from pokedex_tui.screens import browser


class PokedexApp(App):
    """A textual app to browse Pokemon stats, with search and filters by name, type and generation"""

    base_dir = Path(pokedex_tui.__file__).resolve().parent
    tcss_path = base_dir / "styles" / "app.tcss"

    CSS_PATH = tcss_path
    TITLE = "Pokédex"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("d", "toggle_dark", "Toggle dark mode"),
        Binding("q", "quit", "Quit app"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app"""
        yield Header(name="Pokédex", show_clock=True)
        yield browser.Browser()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = PokedexApp()
    app.run()
