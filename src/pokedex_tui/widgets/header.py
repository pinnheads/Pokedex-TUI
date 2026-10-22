from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class PokedexHeader(Horizontal):
    """Custom pokedex header with current results output"""

    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
        all_records,
    ) -> None:
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.total_pokemon = len(all_records)
        self.title = "POKÉDEX"
        self.subtitle = "National Dex Browser"

    def compose(self) -> ComposeResult:
        yield Static(self.title, id="title")
        yield Static(self.subtitle, id="subtitle")
        yield Count(total_count=self.total_pokemon)


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
        total_count: int = 1215,
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
