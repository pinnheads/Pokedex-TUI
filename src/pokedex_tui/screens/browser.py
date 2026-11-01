from collections.abc import Mapping

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
        ranks: Mapping[str, int],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.all_records = all_records
        self.changed_key = all_records[0].key
        self.ranks = ranks

    def on_selection_changed(self, event: Results.SelectionChanged) -> None:
        self.changed_key = event.key
        self.query_one(StatsPanel).show_pokemon(
            pokemon=self.key_to_pokemon(self.changed_key),
            rank=self.ranks[self.changed_key],
            total_count=len(self.all_records),
        )

    def key_to_pokemon(self, key: str) -> Pokemon:
        for pokemon in self.all_records:
            if pokemon.key == key:
                return pokemon
        return self.all_records[0]

    def compose(self) -> ComposeResult:
        """Show Header, Footer and Content"""
        yield PokedexHeader(total=len(self.all_records))
        yield FilterBar()
        with Horizontal(id="body"):
            yield Results(all_records=self.all_records, id="results")
            yield StatsPanel()
        yield Footer()
