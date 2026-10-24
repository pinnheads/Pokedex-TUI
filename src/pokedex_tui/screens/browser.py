from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer

from pokedex_tui.models import Pokemon
from pokedex_tui.widgets.box import Box
from pokedex_tui.widgets.header import PokedexHeader
from pokedex_tui.widgets.results import Results


class Browser(Screen):
    """Browser Screen for the main app"""

    def __init__(
        self,
        data: tuple[Pokemon, ...],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.data = data

    def compose(self) -> ComposeResult:
        """Show Header, Footer and Content"""
        yield PokedexHeader(total=len(self.data))
        yield Search()
        yield Results(all_records=self.data, id="results")
        yield Footer()


class Search(Horizontal):
    """Search bar widgets"""

    def compose(self) -> ComposeResult:
        yield Box(title="Search", id="search-bar")
        yield Box(title="Type", id="type-filter")
        yield Box(title="and Type", id="type-2-filter")
        yield Box(title="Gen", id="gen-filter")
        yield Box(title="Sort", id="sort")
