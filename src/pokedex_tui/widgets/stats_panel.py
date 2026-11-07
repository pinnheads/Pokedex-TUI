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

    def compose(self) -> ComposeResult:
        """Adds these widgets to screen, data is added later"""
        yield Static(classes="name-line")
        yield Static(classes="form-line")
        yield Horizontal(classes="types-container")
        yield Static(classes="stat-rows")
        yield Static(classes="total-row")
        yield Static("enter: full details", classes="hint-line")

    def _get_name_text(self, dex_id: int, name: str) -> Text:
        """Create a Rich Text formatted name and dex_id line for the details panel"""
        return Text(
            text=f"#{dex_id:04} ", style=Style(color=PALETTE.muted_text)
        ).append(text=name, style=Style(bold=True))

    def _get_form_text(self, form: str | None) -> Text:
        """Create a Rich Text formatted form line for the details panel"""
        return Text(text=form or "", style=Style(color=PALETTE.accent))

    def _get_type_container(
        self,
        generation: int,
        types: tuple[str] | tuple[str, str],
        types_container: Horizontal,
    ) -> None:
        """Adds the types and gen to the existing types container"""
        # remove old type badges
        types_container.remove_children()

        # add new type badges
        for type_name in types:
            types_container.mount(TypeBadge(type_name))
        # mount the generation Static widget to the same container
        types_container.mount(Static(f"Gen {generation}", classes="generation"))

    def _get_stat_rows(self, stats: tuple[int, ...]) -> Text:
        """Creates Text representation of pokemon stat rows"""
        rows = Text("")
        for label, stat in zip(LABELS, stats, strict=True):
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

        return rows

    def _get_total_line(self, total: int, rank: int, total_pokemon: int) -> Text:
        total_label = Text(text="Total ", style=Style(color=PALETTE.muted_text))
        total_label.set_length(7)
        total_value = Text(
            text=f"{total}",
            style=Style(color=PALETTE.accent, bold=True),
        )
        total_value.align("right", 4)
        rank_line = Text(
            text=f" rank #{rank} of {total_pokemon}",
            style=Style(color=PALETTE.muted_text),
        )
        return total_label.append(text=total_value).append(text=rank_line)

    def show_pokemon(self, pokemon: Pokemon, rank: int, total_count: int) -> None:
        """Create the final stat panel based on the values passed"""

        # name line
        self.query_one(
            selector=".name-line", expect_type=Static
        ).content = self._get_name_text(dex_id=pokemon.dex_id, name=pokemon.name)

        # form line
        self.query_one(
            selector=".form-line", expect_type=Static
        ).content = self._get_form_text(form=pokemon.form)

        # types line
        container = self.query_one(selector=".types-container", expect_type=Horizontal)
        self._get_type_container(
            generation=pokemon.generation,
            types=pokemon.types,
            types_container=container,
        )

        # stat rows
        self.query_one(
            selector=".stat-rows", expect_type=Static
        ).content = self._get_stat_rows(stats=pokemon.stats)

        # total row
        self.query_one(
            selector=".total-row", expect_type=Static
        ).content = self._get_total_line(
            total=pokemon.total, rank=rank, total_pokemon=total_count
        )

    def clear_pokemon(self):
        self.query_one(".name-line", Static).content = ""
        self.query_one(".form-line", Static).content = ""
        self.query_one(".stat-rows", Static).content = ""
        self.query_one(".total-row", Static).content = ""
        self.query_one(".types-container", Horizontal).remove_children()
