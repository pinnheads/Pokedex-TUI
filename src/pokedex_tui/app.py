from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar

from textual.app import App
from textual.binding import Binding, BindingType
from textual.driver import Driver
from textual.reactive import reactive
from textual.types import CSSPathType
from textual.widgets import Input, Select

from pokedex_tui.loader import PokedexDataError, load_pokemon
from pokedex_tui.models import DEFAULT_SORT, Criteria, Pokemon
from pokedex_tui.query import default_sort_pokemon, filter_and_sort, total_ranks
from pokedex_tui.screens.browser import Browser
from pokedex_tui.theme import APP_THEME
from pokedex_tui.widgets.filter_bar import FilterBar
from pokedex_tui.widgets.header import PokedexHeader
from pokedex_tui.widgets.results import Results


class PokedexApp(App):
    """A textual app to browse Pokemon stats, with search and filters by name, type and generation"""

    def __init__(
        self,
        driver_class: type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
        ansi_color: bool | None = None,
        csv_path: str | Path | None = None,
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.all_records: tuple[Pokemon, ...] = ()
        self.total_ranks: Mapping[str, int] = {}
        self.csv_path = csv_path
        self.register_theme(APP_THEME)
        self.theme = APP_THEME.name
        self.filtered_records = ()

    CSS_PATH = "styles/app.tcss"
    TITLE = "Pokédex"
    ENABLE_COMMAND_PALETTE = False
    criteria = reactive(Criteria(), init=False)
    sort_order = reactive(DEFAULT_SORT, init=False)

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit"),
        Binding("/", "focus_search", "Search"),
        Binding("t", "open_picker_one", "Type"),
        Binding("T", "open_picker_two", "Type", show=False),
        Binding("g", "open_picker_generation", "Gen"),
    ]

    def action_focus_search(self) -> None:
        self.screen.query_one("#search-input", Input).focus()

    def action_open_picker_one(self) -> None:
        self.screen.query_one(
            selector="#type-1-select", expect_type=Select
        ).focus().expanded = True

    def action_open_picker_two(self) -> None:
        self.screen.query_one(
            selector="#type-2-select", expect_type=Select
        ).focus().expanded = True

    def action_open_picker_generation(self) -> None:
        self.screen.query_one(
            selector="#gen-select", expect_type=Select
        ).focus().expanded = True

    def watch_criteria(self) -> None:
        self.update_filtered_records()
        self.screen.query_one(FilterBar)._refresh_pickers()

    def watch_sort_order(self) -> None:
        self.update_filtered_records()

    def update_filtered_records(self) -> None:
        self.filtered_records = filter_and_sort(
            self.all_records, self.criteria, self.sort_order
        )
        result_widget = self.screen.query_one(Results)
        result_widget.update_records(self.filtered_records)
        # update live match count
        header = self.screen.query_one(PokedexHeader)
        header.set_header_match_count(len(self.filtered_records))

    def on_filter_bar_criteria_changed(self, event: FilterBar.CriteriaChanged):
        self.criteria = event.criteria

    def on_filter_bar_sort_changed(self, event: FilterBar.SortChanged):
        self.sort_order = event.sort_order

    def on_mount(self) -> None:
        """Load pokemon csv data and push browser screen"""
        try:
            all_records = default_sort_pokemon(load_pokemon(self.csv_path))
            self.total_ranks = total_ranks(all_records)
            self.all_records = all_records
            self.filtered_records = all_records
            self.push_screen(Browser(all_records=all_records, ranks=self.total_ranks))
        except PokedexDataError as e:
            self.exit(message=str(e), return_code=1)
