from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Header

from pokedex_tui.models import Pokemon


class Browser(Screen):
    """Browser Screen for the main app"""

    def __init__(
        self,
        data: list[Pokemon],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.data = data

    def compose(self) -> ComposeResult:
        """Show Header, Footer and Content"""
        yield Header(name="Pokédex", show_clock=True)
        yield Search()
        yield Box(id="results", title="Results")
        yield Footer()


class Search(Horizontal):
    """Search bar widgets"""

    def compose(self) -> ComposeResult:
        yield Box(title="Search", id="search-bar")
        yield Box(title="Type", id="type-filter")
        yield Box(title="and Type", id="type-2-filter")
        yield Box(title="Gen", id="gen-filter")
        yield Box(title="Sort", id="sort")


class Box(Container):
    """Generic container with ability to set title and subtitle"""

    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
        title: str | None = None,
        subtitle: str | None = None,
    ) -> None:
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.title = title
        self.subtitle = subtitle

    def on_mount(self) -> None:
        """Set title and subtitle if present via instance attribute"""
        if self.title is not None:
            self.border_title = self.title
        if self.subtitle is not None:
            self.border_subtitle = self.subtitle
