from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable

from pokedex_tui.models import Pokemon
from pokedex_tui.widgets.box import Box


class Results(Widget):
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

    def compose(self) -> ComposeResult:
        with Box(title="Results"):
            yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_column("#")
        table.add_column("Name", width=35)
        table.add_column("Types", width=20)
        table.add_column(Text("Total", justify="right"), width=5)
        self.update_records(self.all_records)

    def update_records(self, records: list[Pokemon]) -> None:
        table = self.query_one(DataTable)
        for pokemon in records:
            table.add_row(
                f"{pokemon.dex_id:04}",
                pokemon.display_name,
                f"{pokemon.types[0]} / {pokemon.types[1]}"
                if len(pokemon.types) > 1
                else f"{pokemon.types[0]}",
                Text(str(pokemon.total), justify="right"),
                key=pokemon.key,
            )
