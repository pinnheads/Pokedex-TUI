from rich.style import Style
from rich.text import Text
from textual.widgets import Static

from pokedex_tui.theme import TYPE_STYLES

BADGE_WIDTH = 10


def type_badge_text(type_name: str, no_color: bool) -> Text:
    """single type badge: the name in capitals, centred in BADGE_WIDTH cells"""
    if no_color:
        badge = Text(f"[{type_name.upper()}]")
    else:
        style = TYPE_STYLES[type_name]
        badge = Text(
            type_name.upper(), style=Style(bgcolor=style.badge, color=style.text)
        )
    badge.align("center", width=BADGE_WIDTH)
    return badge


def type_badges_text(types: tuple[str, ...], no_color: bool) -> Text:
    """Every badge for one Pokemon, with one space between them"""
    return Text(" ").join(
        type_badge_text(type_name=name, no_color=no_color) for name in types
    )


class TypeBadge(Static):
    def __init__(
        self,
        type_name: str | None = None,
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
        self.type_name = type_name
        self.styles.width = BADGE_WIDTH

    def on_mount(self) -> None:
        self.set_type(name=self.type_name)

    def set_type(self, name: str | None = None) -> None:
        if name is not None:
            self.display = True
            self.type_name = name
            self.update(
                type_badge_text(type_name=self.type_name, no_color=self.app.no_color)
            )
        else:
            self.display = False
