from typing import TYPE_CHECKING, cast

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input

from pokedex_tui.models import Criteria, SortOrder
from pokedex_tui.widgets.box import Box

if TYPE_CHECKING:
    from pokedex_tui.app import PokedexApp

SEARCH_DEBOUNCE = 0.12


class FilterBar(Horizontal):
    """Filter bar widgets"""

    def __init__(self):
        super().__init__()
        self.timer = None
        self.pokedex_app = cast("PokedexApp", self.app)

    class CriteriaChanged(Message):
        def __init__(self, criteria: Criteria) -> None:
            super().__init__()
            self.criteria = criteria

    class SortChanged(Message):
        def __init__(self, sort_order: SortOrder) -> None:
            super().__init__()
            self.sort_order = sort_order

    def on_input_changed(self, event) -> None:
        # close any previous running timer
        if self.timer:
            self.timer.stop()
        # start a new timer with callback to emit custom message when timer ends
        self.timer = self.set_timer(SEARCH_DEBOUNCE, self._send_search)

    def _send_search(self) -> None:
        current_input_val = self.query_one("#search-input", Input).value
        self.post_message(
            self.CriteriaChanged(
                self.pokedex_app.criteria.replace(search=current_input_val)
            )
        )

    def compose(self) -> ComposeResult:
        yield Box(
            Input(placeholder="Name or Form", id="search-input", compact=True),
            title="Search",
            id="search-bar",
        )
        yield Box(FilterValue("Any", arrow=True), title="Type", id="type-filter")
        yield Box(FilterValue("Any", arrow=True), title="and Type", id="type-2-filter")
        yield Box(FilterValue("All", arrow=True), title="Gen", id="gen-filter")
        yield Box(FilterValue("Dex # ascending"), title="Sort", id="sort")


class FilterValue(Widget, can_focus=True):
    """Placeholder value for a filter box until U5 to U8 add the real controls"""

    def __init__(self, value: str, arrow: bool = False) -> None:
        super().__init__()
        self.value = value
        self.arrow = arrow

    def render(self) -> Text:
        if not self.arrow:
            return Text(self.value)
        return Text(self.value.ljust(max(self.size.width - 1, 0)) + "▼")
