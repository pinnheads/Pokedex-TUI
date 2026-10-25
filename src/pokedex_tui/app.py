from pathlib import Path
from typing import ClassVar

from textual.app import App
from textual.binding import Binding, BindingType
from textual.driver import Driver
from textual.types import CSSPathType

from pokedex_tui.loader import PokedexDataError, load_pokemon
from pokedex_tui.models import Pokemon
from pokedex_tui.query import default_sort_pokemon
from pokedex_tui.screens.browser import Browser
from pokedex_tui.theme import APP_THEME


class PokedexApp(App):
    """A textual app to browse Pokemon stats, with search and filters by name, type and generation"""

    def __init__(
        self,
        driver_class: type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
        ansi_color: bool | None = None,
        csv_path: str | Path | None = None,
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.all_records: tuple[Pokemon, ...] = ()
        self.csv_path = csv_path

    CSS_PATH = "styles/app.tcss"
    TITLE = "Pokédex"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Load pokemon csv data and push browser screen"""
        self.register_theme(APP_THEME)
        self.theme = "pokedex"
        try:
            all_records = default_sort_pokemon(load_pokemon(self.csv_path))
            self.all_records = all_records
            self.push_screen(Browser(all_records=all_records))
        except PokedexDataError as e:
            self.exit(message=str(e), return_code=1)
