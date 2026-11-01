from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer

from pokedex_tui.models import Pokemon
from pokedex_tui.widgets.filter_bar import FilterBar
from pokedex_tui.widgets.header import PokedexHeader
from pokedex_tui.widgets.results import Results
from pokedex_tui.widgets.stats_panel import StatsPanel


class Browser(Screen):
    """Browser Screen for the main app"""

    def __init__(
        self,
        all_records: tuple[Pokemon, ...],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.all_records = all_records

    def compose(self) -> ComposeResult:
        """Show Header, Footer and Content"""
        yield PokedexHeader(total=len(self.all_records))
        yield FilterBar()
        with Horizontal(id="body"):
            yield Results(all_records=self.all_records, id="results")
            yield StatsPanel()
        yield Footer()
