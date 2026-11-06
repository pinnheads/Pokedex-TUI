from typing import TYPE_CHECKING, ClassVar, cast

from rich.align import AlignMethod
from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Static
from textual.events import Click

from pokedex_tui.models import Pokemon, SortOrder
from pokedex_tui.theme import PALETTE
from pokedex_tui.widgets.box import Box
from pokedex_tui.widgets.type_badge import BADGE_WIDTH, type_badges_text


if TYPE_CHECKING:
    from pokedex_tui.app import PokedexApp

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

COLUMN_SORT_FIELDS: dict[str, str] = {"dex_id": "dex", "name": "name", "total": "total"}


def column_at(x: int) -> str | None:
    """The key of the column at this x position in the headings line if any"""
    start = 0
    for key, _, width, _ in COLUMNS:
        end = start + width + 2 * CELL_PADDING
        if start <= x < end:
            return key
        start = end
    return None


class Results(Widget):
    """Displays match results for the pokemon data"""

    class ExtendedTable(DataTable):
        """Subclass of datatable for extending the default Keybinds"""

        BINDINGS: ClassVar[list[BindingType]] = [
            Binding("1", "pick_generation(1)", "Gen 1", show=False),
            Binding("2", "pick_generation(2)", "Gen 2", show=False),
            Binding("3", "pick_generation(3)", "Gen 3", show=False),
            Binding("4", "pick_generation(4)", "Gen 4", show=False),
            Binding("5", "pick_generation(5)", "Gen 5", show=False),
            Binding("6", "pick_generation(6)", "Gen 6", show=False),
            Binding("7", "pick_generation(7)", "Gen 7", show=False),
            Binding("8", "pick_generation(8)", "Gen 8", show=False),
            Binding("9", "pick_generation(9)", "Gen 9", show=False),
            Binding("j", "cursor_down", "Cursor Down", show=False),
            Binding("k", "cursor_up", "Cursor Up", show=False),
            Binding("home", "scroll_top", "Top", show=False),
            Binding("end", "scroll_bottom", "Bottom", show=False),
            Binding("down", "cursor_down", "Move", key_display="↑↓"),
        ]

        def action_pick_generation(self, gen: int) -> None:
            pokedex_app = cast("PokedexApp", self.app)
            if pokedex_app.criteria.generations == frozenset({gen}):
                pokedex_app.criteria = pokedex_app.criteria.replace(
                    generations=frozenset()
                )
            else:
                pokedex_app.criteria = pokedex_app.criteria.replace(
                    generations=frozenset({gen})
                )

    class SelectionChanged(Message):
        """Event emitted when the selection changes on the results table"""

        def __init__(self, key: str):
            super().__init__()
            self.key = key

    class SelectionCleared(Message):
        """Event emitted when the selection is cleared"""

        def __init__(self) -> None:
            super().__init__()

    class SortClicked(Message):
        """Event emitted when a sortable column heading is clicked"""

        def __init__(self, sort_order: SortOrder) -> None:
            super().__init__()
            self.sort_order = sort_order

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
        """
        Headings for the table columns, using the same widths as the table
        with an arrow on the column the table is sorted by
        """
        order = cast("PokedexApp", self.app).sort_order
        arrow = "▼" if order.descending else "▲"
        padding = " " * CELL_PADDING
        headings = Text("")
        for key, heading, width, alignment in COLUMNS:
            is_sorted = COLUMN_SORT_FIELDS.get(key) == order.by
            left = padding
            if is_sorted and alignment == "right":
                left = arrow + padding[1:]
            elif is_sorted:
                heading = heading + arrow
            cell = Text(heading)
            cell.align(alignment, width=width)
            headings.append(left).append(cell).append(padding)
        return headings

    def on_click(self, event: Click) -> None:
        """Sort by the column whose heading was clicked"""
        headings = self.query_one(".headings", Static)
        if event.widget is not headings:
            return
        field = COLUMN_SORT_FIELDS.get(
            column_at(event.screen_x - headings.region.x) or ""
        )
        if field is None:
            return
        current = cast("PokedexApp", self.app).sort_order
        if field == current.by:
            new_order = current.flipped()
        else:
            new_order = SortOrder.for_field(field)
        self.post_message(self.SortClicked(new_order))

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
        self.query_one(".headings", Static).update(self.header_row_text())
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
        # focus on table only when the table was hidden from the empty state message
        if not table.display:
            table.display = True
            table.focus(scroll_visible=False)
        self.query_one("#empty-message").display = False

        if self.selected_key and self.selected_key in self.row_positions:
            self._pending_key = self.selected_key
            table.move_cursor(row=self.row_positions[self.selected_key], scroll=True)
        else:
            self._pending_key = next(iter(self.row_positions))
            table.move_cursor(row=0, scroll=True)
