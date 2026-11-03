from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget

from pokedex_tui.models import Criteria, SortOrder
from pokedex_tui.widgets.box import Box


class FilterBar(Horizontal):
    """Filter bar widgets"""

    class CriteriaChanged(Message):
        def __init__(self, criteria: Criteria) -> None:
            super().__init__()
            self.criteria = criteria

    class SortChanged(Message):
        def __init__(self, sort_order: SortOrder) -> None:
            super().__init__()
            self.sort_order = sort_order

    def compose(self) -> ComposeResult:
        yield Box(FilterValue(""), title="Search", id="search-bar")
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
