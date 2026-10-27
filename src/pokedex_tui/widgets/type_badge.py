from textual.visual import VisualType
from textual.widgets import Static

from pokedex_tui.theme import TYPE_STYLES


class TypeBadge(Static):
    def __init__(
        self,
        type_name: str,
        content: VisualType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.type_name = type_name
        self.style = TYPE_STYLES[type_name]

    def on_mount(self) -> None:
        if self.app.no_color:
            self.update(f"[{self.type_name.upper()}]")
        else:
            self.update(self.type_name.upper())
            self.styles.background = self.style.badge
            self.styles.color = self.style.text

    def update(self, content: VisualType = "", *, layout: bool = True) -> None:
        return super().update(content, layout=layout)
