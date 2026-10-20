from pathlib import Path
from typing import ClassVar

from textual.app import App
from textual.binding import Binding, BindingType
from textual.driver import Driver
from textual.types import CSSPathType

import pokedex_tui
from pokedex_tui.loader import PokedexDataError, load_pokemon
from pokedex_tui.models import Pokemon
from pokedex_tui.screens.browser import Browser


def get_data() -> list[Pokemon]:
    """Gets csv data for the TUI screens"""
    return


class PokedexApp(App):
    """A textual app to browse Pokemon stats, with search and filters by name, type and generation"""

    def __init__(
        self,
        driver_class: type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
        ansi_color: bool | None = None,
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)

    base_dir = Path(pokedex_tui.__file__).resolve().parent
    tcss_path = base_dir / "styles" / "app.tcss"

    CSS_PATH = tcss_path
    TITLE = "Pokédex"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("d", "toggle_dark", "Toggle dark mode"),
        Binding("q", "quit", "Quit app"),
    ]

    def on_mount(self) -> None:
        try:
            data = sorted(
                load_pokemon(), key=lambda pokemon: (pokemon.dex_id, pokemon.is_form)
            )
            print(data)
            self.push_screen(Browser(name="Browser", data=data))
        except PokedexDataError as e:
            print(e.message)
            self.exit()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
