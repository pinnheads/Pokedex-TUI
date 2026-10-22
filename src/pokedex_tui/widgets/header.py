from textual.app import ComposeResult
from textual.containers import Horizontal
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
        self.current_pokemon = self.total_pokemon
        self.title = "POKÉDEX"
        self.subtitle = "National Dex Browser"

    def compose(self) -> ComposeResult:
        yield Static(self.title)
        yield Static(self.subtitle)
        yield Static(f"{self.current_pokemon} of {self.total_pokemon}")
