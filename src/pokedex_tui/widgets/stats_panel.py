from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from pokedex_tui.models import Pokemon
from pokedex_tui.theme import PALETTE


class StatsPanel(Vertical):
    BORDER_TITLE = "Details"
    DEFAULT_CSS = """
    StatsPanel {
        background: $raised;
        height: auto;
        border: solid $border-blurred;
    }
    """

    def compose(self) -> ComposeResult:
        """Adds this widgets to screen, data is added later"""
        yield Static(classes="name-line")
        yield Static(classes="form-line")
        yield Horizontal(classes="types-container")
        yield Static(classes="stat-rows")
        yield Static(classes="total-row")
        yield Static("enter: full details", classes="hint-line")

    def show_pokemon(self, pokemon: Pokemon, rank: int, total_count: int):
        # name line
        self.query_one(selector=".name-line", expect_type=Static).content = Text(
            text=f"{pokemon.dex_id:04} ", style=Style(color=PALETTE.muted_text)
        ).append(text=pokemon.name, style=Style(bold=True))
