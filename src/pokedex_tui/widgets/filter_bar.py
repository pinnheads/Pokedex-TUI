from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message

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
        yield Box(title="Search", id="search-bar")
        yield Box(title="Type", id="type-filter")
        yield Box(title="and Type", id="type-2-filter")
        yield Box(title="Gen", id="gen-filter")
        yield Box(title="Sort", id="sort")
