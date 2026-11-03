from typing import ClassVar

from rich.align import AlignMethod
from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Static

from pokedex_tui.models import Pokemon
from pokedex_tui.theme import PALETTE
from pokedex_tui.widgets.box import Box
from pokedex_tui.widgets.type_badge import BADGE_WIDTH, type_badges_text

# Spaces the table puts on each side of every cell
CELL_PADDING = 1

# (key, heading, width, alignment) for each table column, left to right
COLUMNS: tuple[tuple[str, str, int, AlignMethod], ...] = (
    ("marker", "", 1, "left"),
    ("dex_id", "#", 4, "left"),
    ("name", "Name", 16, "left"),
    ("types", "Types", 2 * BADGE_WIDTH + 1, "left"),
    ("total", "Total", 5, "right"),
)


class Results(Widget):
    """Displays match results for the pokemon data"""

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

    class SelectionCleared(Message):
        def __init__(self) -> None:
            super().__init__()

    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
        all_records: tuple[Pokemon, ...],
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
        self.selected_key: str | None = None
        self._pending_key: str | None = None
        self.row_positions: dict = {}

    def compose(self) -> ComposeResult:
        with Box(title="Results"):
            yield Static(self.header_row_text(), classes="headings")
            yield self.ExtendedTable(cursor_type="row")
            yield Static(
                content="No Pokémon match these filters. Press r to reset.",
                id="empty-message",
            )

    def header_row_text(self) -> Text:
        """Headings for the table columns, using the same widths as the table"""
        padding = " " * CELL_PADDING
        headings = Text("")
        for _, heading, width, alignment in COLUMNS:
            cell = Text(heading)
            cell.align(alignment, width=width)
            headings.append(padding).append(cell).append(padding)
        return headings

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Updates marker position based on the highlighted row"""

        if event.row_key.value is None:
            return

        if self._pending_key and event.row_key.value != self._pending_key:
            return

        if self._pending_key and event.row_key.value == self._pending_key:
            self._pending_key = None
        elif not self._pending_key and self.selected_key == event.row_key.value:
            return

        self.selected_key = event.row_key.value
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
        table.show_header = False
        if self.app.no_color:
            table.add_class("no-color-table")

        # Add all relevant columns
        for key, heading, width, alignment in COLUMNS:
            table.add_column(Text(heading, justify=alignment), width=width, key=key)
        # Update records of current pokemon from the csv
        self.update_records(self.all_records)

    def update_records(self, records: tuple[Pokemon, ...]) -> None:
        """Update records passed in as a tuple[Pokemon, ...]"""
        table = self.query_one(DataTable)
        table.clear()
        self.current_marker = None
        self.row_positions = {}
        for pokemon in records:
            row_key = table.add_row(
                "",
                Text(f"{pokemon.dex_id:04}", style=Style(color=PALETTE.muted_text)),
                pokemon.display_name,
                type_badges_text(pokemon.types, self.app.no_color),
                Text(str(pokemon.total), justify="right"),
                key=pokemon.key,
            )
            self.row_positions[pokemon.key] = table.get_row_index(row_key)

        # Check if there are no rows
        if not self.row_positions:
            self.selected_key = None
            message = self.SelectionCleared()
            self.post_message(message)
            # hide table and headings when no rows to display
            self.query_one(".headings", Static).display = False
            table.display = False
            # show appropriate message to the user on empty rows
            self.query_one("#empty-message").display = True
            return

        # show rows and turn off empty rows message if there are rows to display
        self.query_one(".headings", Static).display = True
        table.display = True
        table.focus(scroll_visible=False)
        self.query_one("#empty-message").display = False

        if self.selected_key and self.selected_key in self.row_positions:
            self._pending_key = self.selected_key
            table.move_cursor(row=self.row_positions[self.selected_key], scroll=True)
        else:
            self._pending_key = next(iter(self.row_positions))
            table.move_cursor(row=0, scroll=True)
