from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header

from pokedex_tui.models import Pokemon


class Browser(Screen):
    """Browser Screen for the main app"""

    def __init__(
        self,
        data: list[Pokemon],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.data = data
        print(self.data)

    def compose(self) -> ComposeResult:
        yield Header(name="Pokédex", show_clock=True)
        yield Footer()
