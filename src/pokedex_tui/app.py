from pathlib import Path
from typing import ClassVar

from textual.app import App
from textual.binding import Binding, BindingType
from textual.driver import Driver
from textual.types import CSSPathType

import pokedex_tui
from pokedex_tui.loader import PokedexDataError, load_pokemon
from pokedex_tui.query import default_sort_pokemon
from pokedex_tui.screens.browser import Browser


class PokedexApp(App):
    """A textual app to browse Pokemon stats, with search and filters by name, type and generation"""

    def __init__(
        self,
        driver_class: type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
        ansi_color: bool | None = None,
        custom_csv: str | Path | None = None,
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.all_records = ()
        self.custom_csv = custom_csv

    base_dir = Path(pokedex_tui.__file__).resolve().parent
    tcss_path = base_dir / "styles" / "app.tcss"

    CSS_PATH = tcss_path
    TITLE = "Pokédex"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Load pokemon csv data and push browser screen"""
        try:
            data = default_sort_pokemon(load_pokemon(self.custom_csv))
            self.all_records = data
            self.push_screen(Browser(name="Browser", data=data))
        except PokedexDataError as e:
            self.exit(message=e.message)
