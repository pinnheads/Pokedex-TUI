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
    return Text(" ").join(type_badge_text(name, no_color) for name in types)


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
        self.type_name = type_name

    def on_mount(self) -> None:
        self.update(type_badge_text(self.type_name, self.app.no_color))
