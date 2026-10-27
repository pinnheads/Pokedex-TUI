from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from pokedex_tui.theme import TYPE_STYLES


class TypeBadge(Widget):
    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
        type_name: str,
    ) -> None:
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.type_name = type_name
        self.style = TYPE_STYLES[self.type_name]

    def compose(self) -> ComposeResult:
        self.widget = Static(self.type_name)
        yield self.widget

    def on_mount(self) -> None:
        self.widget.styles.background = self.style.badge
        self.widget.styles.color = self.style.text
