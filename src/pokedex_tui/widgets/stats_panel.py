from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from pokedex_tui.models import Pokemon
from pokedex_tui.theme import PALETTE
from pokedex_tui.widgets.type_badge import TypeBadge


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
        # form line
        self.query_one(selector=".form-line", expect_type=Static).content = Text(
            text=pokemon.form or "", style=Style(color=PALETTE.accent)
        )
        # types line
        types_container = self.query_one(
            selector=".types-container", expect_type=Horizontal
        )
        # remove all childern of the horizontal container
        types_container.remove_children()
        for type_name in pokemon.types:
            types_container.mount(TypeBadge(type_name=type_name))
        # mount gen name to the same container
        types_container.mount(Static(f"Gen {pokemon.generation}", classes="generation"))
