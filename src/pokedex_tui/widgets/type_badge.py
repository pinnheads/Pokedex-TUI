from rich.style import Style
from rich.text import Text
from textual.widgets import Static

from pokedex_tui.theme import TYPE_STYLES


class TypeBadge(Static):
    def __init__(
        self,
        type_name: str,
        expand: bool = False,
        shrink: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            content="",
            expand=expand,
            shrink=shrink,
            markup=False,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.type_name = type_name.upper()
        self.style = TYPE_STYLES[type_name]

    def on_mount(self) -> None:
        if self.app.no_color:
            self.update(f"[{self.type_name}]")
        else:
            self.update(self.type_name)
            self.styles.background = self.style.badge
            self.styles.color = self.style.text

    def create_text_type_badge(self):
        if self.app.no_color:
            return Text(f"[{self.type_name}]")
        return Text(
            self.type_name, style=Style(bgcolor=self.style.badge, color=self.style.text)
        )


def create_type_badge(types: tuple[str] | tuple[str, str]):
    """Creates type badges for the results table"""
    type_badge_text = Text("")
    for type in types:
        style = TYPE_STYLES[type]
        if type_badge_text:
            type_badge_text.append(" ")
        single_type = Text(
            type.upper(), style=Style(bgcolor=style.badge, color=style.text)
        )
        single_type.align("center", width=10)
        type_badge_text.append(text=single_type)
    return type_badge_text
