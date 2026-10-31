from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from pokedex_tui.models import Pokemon
from pokedex_tui.theme import BAR_WIDTH, PALETTE, band_colour, filled_cells
from pokedex_tui.widgets.type_badge import TypeBadge

LABELS = ("HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed")


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
        """Adds these widgets to screen, data is added later"""
        yield Static(classes="name-line")
        yield Static(classes="form-line")
        yield Horizontal(classes="types-container")
        yield Static(classes="stat-rows")
        yield Static(classes="total-row")
        yield Static("enter: full details", classes="hint-line")

    def show_pokemon(self, pokemon: Pokemon, rank: int, total_count: int) -> None:

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

        # stat rows
        rows = Text("")
        for label, stat in zip(LABELS, pokemon.stats, strict=True):
            # add two newlines every time except for the first line
            if rows:
                rows.append("\n\n")
            label_text = Text(text=label, style=Style(color=PALETTE.muted_text))
            label_text.set_length(8)
            stat_value_text = Text(text=f"{stat}", style=Style(bold=True))
            stat_value_text.align(align="right", width=3)
            filled_cells_text = Text(
                text="█" * filled_cells(stat), style=Style(color=band_colour(stat))
            )
            remaining_cells_text = Text(
                text="░" * (BAR_WIDTH - filled_cells(stat)),
                style=Style(color=PALETTE.bar_track),
            )
            (
                rows.append(text=label_text)
                .append(text=stat_value_text)
                .append(text=" ")
                .append(text=filled_cells_text)
                .append(text=remaining_cells_text)
            )
        self.query_one(selector=".stat-rows", expect_type=Static).content = rows

        # total row
        total_label = Text(text="Total ", style=Style(color=PALETTE.muted_text))
        total_label.set_length(8)
        total_value = Text(
            text=f"{pokemon.total}",
            style=Style(color=PALETTE.accent, bold=True),
        )
        total_value.align("right", 4)
        rank_line = Text(
            text=f" rank #{rank} of {total_count}",
            style=Style(color=PALETTE.muted_text),
        )
        total_line = total_label.append(text=total_value).append(text=rank_line)
        self.query_one(selector=".total-row", expect_type=Static).content = total_line
