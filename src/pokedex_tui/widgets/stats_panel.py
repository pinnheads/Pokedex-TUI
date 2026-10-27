from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static

from pokedex_tui.models import Pokemon
from pokedex_tui.theme import PALETTE
from pokedex_tui.widgets.box import Box
from pokedex_tui.widgets.type_badge import TypeBadge


class StatsPanel(Widget):
    def __init__(
        self,
        pokemon: Pokemon,
        rank: int,
        *children: Widget,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            *children, name="", id=id, classes=classes, disabled=False, markup=False
        )
        self.pokemon = pokemon
        self.rank = rank

    def compose(self) -> ComposeResult:
        with Box(title="Details"):
            # Line 1
            yield Static(
                Text(
                    f"#{self.pokemon.dex_id:04} ",
                    style=Style(color=PALETTE.muted_text),
                ).append(
                    Text(self.pokemon.name, style=Style(bold=True, color=PALETTE.text))
                )
            )
            # Line 2
            if self.pokemon.form is not None:
                yield Static(Text(self.pokemon.form, style=Style(color=PALETTE.accent)))
            else:
                yield Static("")
            # Line 3
            if self.pokemon.type2 is not None:
                yield Horizontal(
                    TypeBadge(self.pokemon.type1),
                    TypeBadge(self.pokemon.type2),
                    Static(
                        Text(
                            f"Gen {self.pokemon.generation}",
                            style=Style(color=PALETTE.muted_text),
                        )
                    ),
                    id="type-gen",
                )
            else:
                yield Horizontal(
                    TypeBadge(self.pokemon.type1),
                    Static(
                        Text(
                            f"Gen {self.pokemon.generation}",
                            style=Style(color=PALETTE.muted_text),
                        )
                    ),
                    id="type-gen",
                )
