from textual.containers import Container
from textual.widget import Widget


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
