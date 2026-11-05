from typing import TYPE_CHECKING, ClassVar, cast

from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Select

from pokedex_tui.models import GENERATIONS, NO_SECOND_TYPE, Criteria, SortOrder
from pokedex_tui.query import type_counts, type_options
from pokedex_tui.theme import PALETTE
from pokedex_tui.widgets.box import Box
from pokedex_tui.widgets.results import Results

if TYPE_CHECKING:
    from pokedex_tui.app import PokedexApp

SEARCH_DEBOUNCE = 0.12
ANY_TYPE = "any"
ANY_GENERATION = 0


class FilterBar(Horizontal):
    """Filter bar widgets"""

    def __init__(self):
        super().__init__()
        self.timer = None

    class CriteriaChanged(Message):
        def __init__(self, criteria: Criteria) -> None:
            super().__init__()
            self.criteria = criteria

    class SortChanged(Message):
        def __init__(self, sort_order: SortOrder) -> None:
            super().__init__()
            self.sort_order = sort_order

    def on_input_submitted(self) -> None:
        self.screen.query_one(Results.ExtendedTable).focus()

    def on_input_changed(self) -> None:
        # close any previous running timer
        if self.timer:
            self.timer.stop()
        # start a new timer with callback to emit custom message when timer ends
        self.timer = self.set_timer(SEARCH_DEBOUNCE, self._send_search)

    def on_select_changed(self, event: Select.Changed) -> None:
        pokedex_app = cast("PokedexApp", self.app)
        current_val = event.value

        # type picker handling
        if event.select.id == "type-1-select" or event.select.id == "type-2-select":
            changed_type = 1 if event.select.id == "type-1-select" else 2
            if current_val == ANY_TYPE:
                current_val = None

            if changed_type == 1 and pokedex_app.criteria.type1 != current_val:
                self.post_message(
                    self.CriteriaChanged(
                        pokedex_app.criteria.replace(type1=current_val)
                    )
                )
                self.screen.query_one(Results.ExtendedTable).focus()

            if changed_type == 2 and pokedex_app.criteria.type2 != current_val:
                self.post_message(
                    self.CriteriaChanged(
                        pokedex_app.criteria.replace(type2=current_val)
                    )
                )
                self.screen.query_one(Results.ExtendedTable).focus()

        current_val = frozenset() if not current_val else frozenset({current_val})
        # generation picker handling
        if (
            event.select.id == "gen-select"
            and pokedex_app.criteria.generations != current_val
        ):
            if current_val == ANY_GENERATION:
                self.post_message(
                    self.CriteriaChanged(
                        pokedex_app.criteria.replace(generations=frozenset())
                    )
                )
            else:
                self.post_message(
                    self.CriteriaChanged(
                        pokedex_app.criteria.replace(
                            generations=frozenset({current_val})
                        )
                    )
                )

    def _refresh_pickers(self) -> None:
        type1 = self.screen.query_one("#type-1-select", Select)
        type2 = self.screen.query_one("#type-2-select", Select)
        gen = self.screen.query_one("#gen-select", Select)

        pokedex_app = cast("PokedexApp", self.app)

        with type1.prevent(Select.Changed):
            type1.set_options(self._get_type_options(1))
            type1.value = (
                pokedex_app.criteria.type1
                if pokedex_app.criteria.type1 is not None
                else ANY_TYPE
            )

        with type2.prevent(Select.Changed):
            type2.set_options(self._get_type_options(2))
            type2.value = (
                pokedex_app.criteria.type2
                if pokedex_app.criteria.type2 is not None
                else ANY_TYPE
            )

        with gen.prevent(Select.Changed):
            gen.set_options(self._get_generation_options())
            gen.value = (
                ANY_GENERATION
                if not pokedex_app.criteria.generations
                else next(iter(pokedex_app.criteria.generations))
            )

    def _send_search(self) -> None:
        current_input_val = self.query_one("#search-input", Input).value
        pokedex_app = cast("PokedexApp", self.app)
        self.post_message(
            self.CriteriaChanged(pokedex_app.criteria.replace(search=current_input_val))
        )

    def _get_generation_options(self) -> tuple[tuple[str, int], ...]:
        gen_options = [("All", ANY_GENERATION)]
        for gen in GENERATIONS:
            gen_options.append((f"{gen}", gen))

        return tuple(gen_options)

    def _get_type_options(self, slot: int) -> tuple[tuple[str | Text, str], ...]:
        original_options = type_options(slot)
        pokedex_app = cast("PokedexApp", self.app)
        counts = type_counts(pokedex_app.all_records, pokedex_app.criteria, slot)
        options_for_display: list[tuple[str | Text, str]] = []
        for option in original_options:
            if option is None:
                options_for_display.append(("Any", ANY_TYPE))
            elif option == NO_SECOND_TYPE:
                options_for_display.append(
                    (
                        self._build_label(text="None", count=counts[NO_SECOND_TYPE]),
                        NO_SECOND_TYPE,
                    )
                )
            else:
                options_for_display.append(
                    (
                        self._build_label(text=option, count=counts[option]),
                        option,
                    )
                )
        return tuple(options_for_display)

    def _build_label(self, text: str, count: int) -> str | Text:
        label = f"{text} ({count})"
        return (
            label if count != 0 else Text(label, style=Style(color=PALETTE.muted_text))
        )

    def on_mount(self) -> None:
        self._refresh_pickers()

    def compose(self) -> ComposeResult:
        yield Box(
            CustomInput(placeholder="name or form", id="search-input", compact=True),
            title="Search",
            id="search-bar",
        )
        yield Box(
            Select(
                id="type-1-select",
                allow_blank=False,
                compact=True,
                options=self._get_type_options(1),
            ),
            title="Type",
            id="type-filter",
        )
        yield Box(
            Select(
                id="type-2-select",
                allow_blank=False,
                compact=True,
                options=self._get_type_options(2),
            ),
            title="and Type",
            id="type-2-filter",
        )
        yield Box(
            Select(
                id="gen-select",
                allow_blank=False,
                compact=True,
                options=self._get_generation_options(),
            ),
            title="Gen",
            id="gen-filter",
        )
        yield Box(FilterValue("Dex # ascending"), title="Sort", id="sort")


class CustomInput(Input):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "focus_table", "Back"),
    ]

    def action_focus_table(self):
        self.screen.query_one(Results.ExtendedTable).focus()


class FilterValue(Widget, can_focus=True):
    """Placeholder value for a filter box until U5 to U8 add the real controls"""

    def __init__(self, value: str, arrow: bool = False) -> None:
        super().__init__()
        self.value = value
        self.arrow = arrow

    def render(self) -> Text:
        if not self.arrow:
            return Text(self.value)
        return Text(self.value.ljust(max(self.size.width - 1, 0)) + "▼")
