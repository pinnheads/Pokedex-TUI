from textual.app import ComposeResult
from textual.containers import Horizontal

from pokedex_tui.widgets.box import Box


class FilterBar(Horizontal):
    """Filter bar widgets"""

    def compose(self) -> ComposeResult:
        yield Box(title="Search", id="search-bar")
        yield Box(title="Type", id="type-filter")
        yield Box(title="and Type", id="type-2-filter")
        yield Box(title="Gen", id="gen-filter")
        yield Box(title="Sort", id="sort")
