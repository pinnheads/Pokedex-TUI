from typing import ClassVar

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable

from pokedex_tui.models import Pokemon
from pokedex_tui.widgets.box import Box


class Results(Widget):
    class ExtendedTable(DataTable):
        """Subclass of datatable for extending the default Keybinds"""

        BINDINGS: ClassVar[list[BindingType]] = [
            Binding("j", "cursor_down", "Cursor Down", show=False),
            Binding("k", "cursor_up", "Cursor Up", show=False),
            Binding("home", "scroll_top", "Top", show=False),
            Binding("end", "scroll_bottom", "Bottom", show=False),
            Binding("down", "cursor_down", "Move", key_display="↑↓"),
        ]

    class SelectionChanged(Message):
        """Event emitted when the selection changes on the results table"""

        def __init__(self, key: str):
            super().__init__()
            self.key = key

    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
        all_records: list[Pokemon],
    ) -> None:
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.all_records = all_records
        self.current_marker = None

    def compose(self) -> ComposeResult:
        with Box(title="Results"):
            yield self.ExtendedTable(cursor_type="row")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        """Updates marker position based on the highlighted row"""

        if event.row_key.value is None:
            return

        # emit an event on current highlighted row change
        self.post_message(self.SelectionChanged(event.row_key.value))

        # current marker change logic
        table = event.data_table
        highlighted_key = event.row_key
        if self.current_marker is not None:
            table.update_cell(self.current_marker, "marker", "")
        table.update_cell(highlighted_key, "marker", ">")
        self.current_marker = highlighted_key

    def on_mount(self) -> None:
        # Get the current datatable
        table = self.query_one(DataTable)
        # Focus on the datatable on mount
        table.focus(scroll_visible=False)

        # Add all relevant columns
        table.add_column("", width=1, key="marker")
        table.add_column("#", key="dex_id")
        table.add_column("Name", width=35)
        table.add_column("Types", width=20)
        table.add_column(Text("Total", justify="right"), width=5)
        # Update records of current pokemon from the csv
        self.update_records(self.all_records)

    def update_records(self, records: list[Pokemon]) -> None:
        """Update records passed in as a list[Pokemon]"""
        table = self.query_one(DataTable)
        table.clear()
        self.current_marker = None
        for pokemon in records:
            table.add_row(
                "",
                f"{pokemon.dex_id:04}",
                pokemon.display_name,
                f"{pokemon.types[0]} / {pokemon.types[1]}"
                if len(pokemon.types) > 1
                else f"{pokemon.types[0]}",
                Text(str(pokemon.total), justify="right"),
                key=pokemon.key,
            )
