from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class PokedexHeader(Horizontal):
    """Custom pokedex header with current results output"""

    TITLE = "POKÉDEX"
    SUBTITLE = "National Dex Browser"

    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
        all_records: int,
    ) -> None:
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.total_pokemon = all_records

    def compose(self) -> ComposeResult:
        yield Static(self.TITLE, id="title")
        yield Static(self.SUBTITLE, id="subtitle")
        yield Count(total_count=self.total_pokemon)

    def set_header_match_count(self, count: int) -> None:
        """Update the current match count on the header"""
        self.query_one(Count).current_count = count


class Count(Widget):
    """
    Creates the count widget for the header

    To update the current_count use:
    `self.query_one(Count).current_count = <actual_count>`
    """

    current_count = reactive(0)

    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = "count",
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
        total_count: int,
    ) -> None:
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.total_count = total_count
        self.current_count = self.total_count

    def render(self) -> str:
        """Method to generate a reactive piece of current count string"""
        return f"{self.current_count} of {self.total_count}"
