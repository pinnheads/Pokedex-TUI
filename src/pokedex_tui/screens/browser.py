from collections.abc import Mapping
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
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

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("/", "app.focus_search", "Search"),
        Binding("t", "app.open_picker_one", "Type"),
        Binding("T", "app.open_picker_two", "Type", show=False),
        Binding("g", "app.open_picker_generation", "Gen"),
        Binding("s", "app.set_next_sort_field", "Sort"),
        Binding("r", "app.reset", "Reset"),
        Binding("S", "app.flip_sort_order", "Sort", show=False),
    ]

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
        self.selected_key: str | None = None
        self.lookup_table = {pokemon.key: pokemon for pokemon in self.all_records}
        self.ranks = ranks

    def on_results_selection_changed(self, event: Results.SelectionChanged) -> None:
        """Updates the stats panel details based on selection change"""
        self.selected_key = event.key
        self.query_one(StatsPanel).show_pokemon(
            pokemon=self.lookup_table[self.selected_key],
            rank=self.ranks[self.selected_key],
            total_count=len(self.all_records),
        )

    def on_results_selection_cleared(self, event: Results.SelectionCleared) -> None:
        self.selected_key = None
        self.query_one(StatsPanel).clear_pokemon()

    def compose(self) -> ComposeResult:
        """Show Header, Footer and Content"""
        yield PokedexHeader(total=len(self.all_records))
        yield FilterBar()
        with Horizontal(id="body"):
            yield Results(all_records=self.all_records, id="results")
            yield StatsPanel()
        yield Footer()
