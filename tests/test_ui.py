"""Phase 2: pilot tests for the read-only browser (S10).

Each test starts the real app headless at 100 x 30 and drives it with keys.

Names these tests expect (rename here if you change them):
- pokedex_tui.app.PokedexApp(custom_csv=...): the App, with an optional CSV path.
- pokedex_tui.widgets.header: PokedexHeader with set_header_match_count(n),
  and Count, which renders "N of M".
- pokedex_tui.widgets.results.Results: holds the DataTable, has
  update_records(records) and posts Results.SelectionChanged(key).
- pokedex_tui.screens.browser.Search: the filter bar.
- Table columns, left to right: marker (key "marker"), #, Name, Types, Total.
"""

import pytest
from rich.text import Text

SIZE = (100, 30)

# Column positions in a table row, see the module docstring.
MARKER, DEX, NAME, TYPES, TOTAL = range(5)


# --- Helpers -------------------------------------------------------------------


def make_app(csv_path=None):
    from pokedex_tui.app import PokedexApp

    return PokedexApp(custom_csv=csv_path)


def table_of(app):
    from textual.widgets import DataTable

    return app.screen.query_one(DataTable)


def count_text(app):
    from pokedex_tui.widgets.header import Count

    return str(app.screen.query_one(Count).render())


def row(table, index):
    return table.get_row_at(index)


def selected_name(table):
    return row(table, table.cursor_row)[NAME]


def marker_rows(table):
    """Indexes of every row whose marker cell shows '>'."""
    return [i for i in range(table.row_count) if str(row(table, i)[MARKER]) == ">"]


async def start(app, pilot):
    """Wait until on_mount has loaded the data and pushed the browser screen."""
    await pilot.pause()


# --- Header (S5) ---------------------------------------------------------------


async def test_header_shows_full_count():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert count_text(app) == "1215 of 1215"


async def test_header_count_comes_from_the_data(small_csv):
    app = make_app(small_csv)
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert count_text(app) == "14 of 14"


async def test_header_title_and_subtitle():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert str(app.screen.query_one("#header-title").render()) == "POKÉDEX"
        assert str(app.screen.query_one("#header-subtitle").render()) == (
            "National Dex Browser"
        )


async def test_header_match_count_can_be_updated():
    from pokedex_tui.widgets.header import PokedexHeader

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.screen.query_one(PokedexHeader).set_header_match_count(9)
        await pilot.pause()
        assert count_text(app) == "9 of 1215"


# --- Layout (S4) -----------------------------------------------------------------


async def test_layout_regions_at_100_by_30():
    from textual.widgets import Footer

    from pokedex_tui.screens.browser import Search
    from pokedex_tui.widgets.header import PokedexHeader
    from pokedex_tui.widgets.results import Results

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        screen = app.screen
        header = screen.query_one(PokedexHeader).region
        search = screen.query_one(Search).region
        results = screen.query_one(Results).region
        footer = screen.query_one(Footer).region

        assert (header.y, header.height) == (0, 1)
        assert (search.y, search.height) == (1, 3)
        assert (results.y, results.height) == (4, 25)
        assert (footer.y, footer.height) == (29, 1)
        assert results.width == 100, "a screen scrollbar is eating columns"
        assert not screen.show_vertical_scrollbar


# --- Results table (S6) ----------------------------------------------------------


async def test_table_has_every_pokemon():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert table_of(app).row_count == 1215


async def test_table_is_in_dex_order_with_forms_after_base():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        firsts = [(row(table, i)[DEX], row(table, i)[NAME]) for i in range(4)]
        assert firsts == [
            ("0001", "Bulbasaur"),
            ("0002", "Ivysaur"),
            ("0003", "Venusaur"),
            ("0003", "Mega Venusaur"),
        ]


async def test_table_dex_numbers_never_go_backwards():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        dex = [int(row(table, i)[DEX]) for i in range(table.row_count)]
        assert dex == sorted(dex)


async def test_every_zygarde_row_is_shown(all_records):
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        expected = sum(1 for p in all_records if p.dex_id == 718)
        shown = sum(1 for i in range(table.row_count) if row(table, i)[DEX] == "0718")
        assert expected >= 2
        assert shown == expected


async def test_types_are_written_out():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        assert str(row(table, 0)[TYPES]) == "Grass / Poison"  # Bulbasaur
        charmander = next(
            i for i in range(table.row_count) if row(table, i)[NAME] == "Charmander"
        )
        assert str(row(table, charmander)[TYPES]) == "Fire"


async def test_total_is_right_aligned():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        total = row(table_of(app), 0)[TOTAL]
        assert isinstance(total, Text)
        assert total.justify == "right"
        assert str(total) == "318"


async def test_update_records_replaces_the_rows():
    from pokedex_tui.widgets.results import Results

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.screen.query_one(Results).update_records(app.all_records[:9])
        await pilot.pause()
        assert table_of(app).row_count == 9


# --- Selection and marker (S7) -----------------------------------------------------


async def test_table_has_focus_and_first_row_selected():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        assert app.focused is table
        assert table.cursor_type == "row"
        assert table.cursor_row == 0
        assert marker_rows(table) == [0]


async def test_marker_follows_the_cursor():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        await pilot.press("down", "down", "down")
        await pilot.pause()
        assert marker_rows(table) == [3]
        await pilot.press("up")
        await pilot.pause()
        assert marker_rows(table) == [2]


async def test_marker_survives_a_refill_that_keeps_the_marked_row():
    """The marked Pokémon lands on the highlighted row after the refill."""
    from pokedex_tui.widgets.results import Results

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        await pilot.press("down")  # Ivysaur
        await pilot.pause()
        app.screen.query_one(Results).update_records(app.all_records[1:10])
        await pilot.pause()
        assert marker_rows(table) == [table.cursor_row]


async def test_moving_after_a_refill_that_drops_the_marked_row():
    from pokedex_tui.widgets.results import Results

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        await pilot.press("down")
        await pilot.pause()
        app.screen.query_one(Results).update_records(app.all_records[100:110])
        await pilot.pause()
        await pilot.press("down")
        await pilot.pause()
        assert marker_rows(table) == [table.cursor_row]


async def test_selection_changed_carries_the_record_key():
    app = make_app()
    keys = []
    async with app.run_test(size=SIZE, message_hook=_collect(keys)) as pilot:
        await start(app, pilot)
        await pilot.press("down")
        await pilot.pause()
        assert keys, "no Results.SelectionChanged was posted"
        assert keys[-1] == app.all_records[1].key
        assert isinstance(keys[-1], str)


def _collect(keys):
    from pokedex_tui.widgets.results import Results

    def hook(message):
        if isinstance(message, Results.SelectionChanged):
            keys.append(message.key)

    return hook


# --- Keyboard navigation (S8) --------------------------------------------------------


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        (("end",), "Pecharunt"),
        (("end", "home"), "Bulbasaur"),
        (("j", "j"), "Venusaur"),
        (("j", "j", "k"), "Ivysaur"),
        (("down", "down", "up"), "Ivysaur"),
    ],
)
async def test_navigation_keys(keys, expected):
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press(*keys)
        await pilot.pause()
        assert selected_name(table_of(app)) == expected


async def test_page_down_moves_a_page_and_keeps_the_row_in_view():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        await pilot.press("pagedown")
        await pilot.pause()
        assert table.cursor_row > 10
        top = table.scroll_offset.y
        visible_rows = table.scrollable_content_region.height - 1  # minus heading
        assert top <= table.cursor_row < top + visible_rows


async def test_end_scrolls_the_last_row_into_view():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        await pilot.press("end")
        await pilot.pause()
        assert table.scroll_offset.y > 0
        assert marker_rows(table) == [1214]


# --- Footer (S9) and quitting ----------------------------------------------------------


async def test_footer_shows_only_working_keys():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        shown = [
            binding.description
            for _, binding, enabled, _ in app.active_bindings.values()
            if binding.show and enabled
        ]
        assert sorted(shown) == ["Move", "Quit"]


async def test_move_key_shows_both_arrows():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        move = next(
            binding
            for _, binding, _, _ in app.active_bindings.values()
            if binding.show and binding.description == "Move"
        )
        assert move.key_display == "↑↓"


async def test_q_quits_from_the_browser():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("q")
        await pilot.pause()
    assert app.return_code == 0
