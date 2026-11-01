"""Phase 2: pilot tests for the read-only browser (S10).

Each test starts the real app headless at 100 x 30 and drives it with keys.

Names these tests expect (rename here if you change them):
- pokedex_tui.app.PokedexApp(csv_path=...): the App, with an optional CSV path.
- pokedex_tui.widgets.header: PokedexHeader with set_header_match_count(n),
  and Count, which renders "N of M".
- pokedex_tui.widgets.results.Results: holds the DataTable, has
  update_records(records) and posts Results.SelectionChanged(key).
- pokedex_tui.widgets.filter_bar.FilterBar: the filter bar.
- Table columns, left to right: marker (key "marker"), #, Name, Types, Total.
"""

import itertools

import pytest
from rich.text import Text

SIZE = (100, 30)

# Column positions in a table row, see the module docstring.
MARKER, DEX, NAME, TYPES, TOTAL = range(5)


# --- Helpers -------------------------------------------------------------------


def make_app(csv_path=None):
    from pokedex_tui.app import PokedexApp

    return PokedexApp(csv_path=csv_path)


def table_of(app):
    from textual.widgets import DataTable

    return app.screen.query_one(DataTable)


def count_text(app):
    from pokedex_tui.widgets.header import Count

    return str(app.screen.query_one(Count).render())


def row(table, index):
    """One table row as plain strings (Rich Text cells become their text)."""
    return [str(cell) for cell in table.get_row_at(index)]


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

    from pokedex_tui.widgets.filter_bar import FilterBar
    from pokedex_tui.widgets.header import PokedexHeader
    from pokedex_tui.widgets.results import Results
    from pokedex_tui.widgets.stats_panel import StatsPanel

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        screen = app.screen
        header = screen.query_one(PokedexHeader).region
        search = screen.query_one(FilterBar).region
        results = screen.query_one(Results).region
        details = screen.query_one(StatsPanel).region
        footer = screen.query_one(Footer).region

        assert (header.y, header.height) == (0, 1)
        assert (search.y, search.height) == (1, 3)
        assert (footer.y, footer.height) == (29, 1)
        # C7: Results on the left (60%), Details on the right (40%), same rows.
        assert (results.x, results.y, results.height) == (0, 4, 25)
        assert (details.y, details.height) == (4, 25)
        assert (results.width, details.width) == (60, 40)
        assert details.x == results.right
        assert details.right == 100, "a screen scrollbar is eating columns"
        assert not screen.show_vertical_scrollbar


async def test_only_the_focused_box_has_an_accent_border():
    """C7: the focused Results box has an accent border and title; Details is grey."""
    from pokedex_tui.theme import PALETTE
    from pokedex_tui.widgets.results import Results
    from pokedex_tui.widgets.stats_panel import StatsPanel

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        screen = app.screen
        for widget, title, border, title_colour in (
            (Results, "Results", PALETTE.accent, PALETTE.accent),
            (StatsPanel, "Details", PALETTE.border, PALETTE.muted_text),
        ):
            region = screen.query_one(widget).region
            top = screen_cells(app, region)[0]
            text = row_text(top)
            start_at = text.index(title)
            title_cells = top[start_at : start_at + len(title)]
            line_cells = [style for char, style in top if char == "─"]

            assert {hex_of(s.color) for _, s in title_cells} == {title_colour}
            assert {hex_of(s.color) for s in line_cells} == {border}


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
        # C8: the types are badges with the name in capitals.
        assert row(table, 0)[TYPES].split() == ["GRASS", "POISON"]  # Bulbasaur
        charmander = next(
            i for i in range(table.row_count) if row(table, i)[NAME] == "Charmander"
        )
        assert row(table, charmander)[TYPES].split() == ["FIRE"]


async def test_total_is_right_aligned():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        total = table_of(app).get_row_at(0)[TOTAL]
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


# --- Phase 3 helpers -------------------------------------------------------------------
#
# C5 (PTI-26) and C6 (PTI-24) are tested on a small test app that shows only
# the widget being tested, with the real theme and stylesheet.
#
# Names these tests expect (rename here if you chose different ones):
# - pokedex_tui.widgets.type_badge.TypeBadge(type_name): one badge.
# - pokedex_tui.widgets.stats_panel.StatsPanel(): the Details panel. It is
#   empty until show_pokemon(pokemon, rank, total_count) is called, and
#   calling show_pokemon again replaces what it shows.

FULL, SHADE = "█", "░"  # full block and light shade
STAT_LABELS = ("HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed")


def make_widget_app(*widgets):
    from pathlib import Path

    from textual.app import App

    import pokedex_tui
    from pokedex_tui.theme import APP_THEME

    css = Path(pokedex_tui.__file__).parent / "styles" / "app.tcss"

    class WidgetApp(App):
        CSS_PATH = str(css)

        def __init__(self):
            super().__init__()
            self.register_theme(APP_THEME)
            self.theme = APP_THEME.name

        def compose(self):
            yield from widgets

    return WidgetApp()


def hex_of(colour):
    return None if colour is None else colour.get_truecolor().hex.lower()


def screen_cells(app, region):
    """The cells inside region, one list of (character, rich Style) per row."""
    strips = app.screen._compositor.render_strips()
    rows = []
    for y in range(region.y, region.bottom):
        cells = []
        for segment in strips[y]:
            cells.extend((char, segment.style) for char in segment.text)
        rows.append(cells[region.x : region.right])
    return rows


def row_text(cells):
    return "".join(char for char, _ in cells)


# --- Type badge (C5) -------------------------------------------------------------------


@pytest.mark.parametrize(
    "type_name",
    [
        "Bug", "Dark", "Dragon", "Electric", "Fairy", "Fighting",
        "Fire", "Flying", "Ghost", "Grass", "Ground", "Ice",
        "Normal", "Poison", "Psychic", "Rock", "Steel", "Water",
    ],
)  # fmt: skip
async def test_badge_shows_the_type_in_capitals_with_its_colours(type_name):
    from pokedex_tui.theme import TYPE_STYLES
    from pokedex_tui.widgets.type_badge import TypeBadge

    badge = TypeBadge(type_name)
    app = make_widget_app(badge)
    async with app.run_test(size=(40, 5)) as pilot:
        await pilot.pause()
        (cells,) = screen_cells(app, badge.region)

        assert row_text(cells).strip() == type_name.upper()
        style = TYPE_STYLES[type_name]
        for _, cell_style in cells:
            assert hex_of(cell_style.bgcolor) == style.badge
        for char, cell_style in cells:
            if char != " ":
                assert hex_of(cell_style.color) == style.text


async def test_every_badge_is_one_row_and_the_same_width():
    from pokedex_tui.models import TYPES
    from pokedex_tui.widgets.type_badge import TypeBadge

    badges = [TypeBadge(name) for name in TYPES]
    app = make_widget_app(*badges)
    async with app.run_test(size=(40, 24)) as pilot:
        await pilot.pause()
        assert {badge.size.height for badge in badges} == {1}
        assert len({badge.size.width for badge in badges}) == 1
        assert badges[0].size.width >= len("[ELECTRIC]")


async def test_badge_name_has_space_on_both_sides():
    from pokedex_tui.widgets.type_badge import TypeBadge

    badge = TypeBadge("Electric")
    app = make_widget_app(badge)
    async with app.run_test(size=(40, 5)) as pilot:
        await pilot.pause()
        text = row_text(screen_cells(app, badge.region)[0])
        assert text.startswith(" ") and text.endswith(" ")
        assert text.strip() == "ELECTRIC"


async def test_badge_with_no_color_shows_the_name_in_brackets(monkeypatch):
    from pokedex_tui.theme import PALETTE, TYPE_STYLES
    from pokedex_tui.widgets.type_badge import TypeBadge

    monkeypatch.setenv("NO_COLOR", "1")
    badge = TypeBadge("Fire")
    app = make_widget_app(badge)
    async with app.run_test(size=(40, 5)) as pilot:
        await pilot.pause()
        (cells,) = screen_cells(app, badge.region)

        assert row_text(cells).strip() == "[FIRE]"
        for _, cell_style in cells:
            assert hex_of(cell_style.bgcolor) != TYPE_STYLES["Fire"].badge
            assert hex_of(cell_style.bgcolor) == PALETTE.background


# --- Stats panel (C6) ------------------------------------------------------------------


def find_pokemon(records, name, form=None):
    return next(p for p in records if p.name == name and p.form == form)


def panel_rows(app, panel):
    return screen_cells(app, panel.content_region)


def line_index(rows, text):
    """Index of the first row containing text."""
    return next(i for i, cells in enumerate(rows) if text in row_text(cells))


def style_of(cells, text):
    """Style of the first character of text within a row."""
    start = row_text(cells).index(text)
    return cells[start][1]


@pytest.fixture
def charizards(all_records):
    return (
        find_pokemon(all_records, "Charizard"),
        find_pokemon(all_records, "Charizard", "Mega Charizard X"),
    )


async def run_panel(all_records, pokemon, *, then=None):
    """Show pokemon (and optionally then another) and return the panel rows."""
    from pokedex_tui.query import total_ranks
    from pokedex_tui.widgets.stats_panel import StatsPanel

    ranks = total_ranks(all_records)
    panel = StatsPanel()
    app = make_widget_app(panel)
    async with app.run_test(size=(60, 30)) as pilot:
        await pilot.pause()
        panel.show_pokemon(pokemon, ranks[pokemon.key], len(all_records))
        await pilot.pause()
        if then is not None:
            panel.show_pokemon(then, ranks[then.key], len(all_records))
            await pilot.pause()
        return panel_rows(app, panel), ranks


async def test_panel_first_line_is_dex_number_and_name(all_records, charizards):
    from pokedex_tui.theme import PALETTE

    rows, _ = await run_panel(all_records, charizards[0])
    first = rows[line_index(rows, "Charizard")]

    assert "0006" in row_text(first)
    assert row_text(first).index("0006") < row_text(first).index("Charizard")
    assert hex_of(style_of(first, "0006").color) == PALETTE.muted_text
    assert style_of(first, "Charizard").bold


async def test_panel_form_line_in_accent(all_records, charizards):
    from pokedex_tui.theme import PALETTE

    rows, _ = await run_panel(all_records, charizards[1])
    name_row = line_index(rows, "Charizard")
    form = rows[name_row + 1]

    assert "Mega Charizard X" in row_text(form)
    assert hex_of(style_of(form, "Mega Charizard X").color) == PALETTE.accent


async def test_base_form_keeps_a_blank_form_line(all_records, charizards):
    base_rows, _ = await run_panel(all_records, charizards[0])
    mega_rows, _ = await run_panel(all_records, charizards[1])

    base_name = line_index(base_rows, "Charizard")
    assert row_text(base_rows[base_name + 1]).strip() == ""
    # The types line sits on the same row for both, so nothing jumps.
    assert line_index(base_rows, "FIRE") == line_index(mega_rows, "FIRE")


@pytest.mark.parametrize(
    ("which", "types", "gen"),
    [(0, ("FIRE", "FLYING"), "Gen 1"), (1, ("FIRE", "DRAGON"), "Gen 6")],
)
async def test_panel_types_line_has_badges_and_generation(
    all_records, charizards, which, types, gen
):
    from pokedex_tui.theme import PALETTE, TYPE_STYLES

    rows, _ = await run_panel(all_records, charizards[which])
    types_line = rows[line_index(rows, types[0])]
    text = row_text(types_line)

    for badge in types:
        assert badge in text
        assert hex_of(style_of(types_line, badge).bgcolor) == (
            TYPE_STYLES[badge.title()].badge
        )
    assert text.index(types[0]) < text.index(types[1]) < text.index(gen)
    assert hex_of(style_of(types_line, gen).color) == PALETTE.muted_text


async def test_panel_single_type_shows_one_badge(all_records):
    charmander = find_pokemon(all_records, "Charmander")
    rows, _ = await run_panel(all_records, charmander)
    text = row_text(rows[line_index(rows, "FIRE")])

    assert "Gen 1" in text
    assert not any(t.upper() in text for t in ("Flying", "Dragon", "Water"))


async def test_panel_stat_rows_in_order_with_a_blank_row_between(
    all_records, charizards
):
    rows, _ = await run_panel(all_records, charizards[0])
    positions = [line_index(rows, label) for label in STAT_LABELS]

    assert positions == sorted(positions)
    for upper, lower in itertools.pairwise(positions):
        assert lower - upper == 2
        assert row_text(rows[upper + 1]).strip() == ""


async def test_panel_stat_values_bars_and_colours(all_records, charizards):
    from pokedex_tui.theme import BAR_WIDTH, PALETTE, band_colour, filled_cells

    mega = charizards[1]
    rows, _ = await run_panel(all_records, mega)
    value_ends = set()

    for label, value in zip(STAT_LABELS, mega.stats, strict=True):
        cells = rows[line_index(rows, label)]
        text = row_text(cells)

        assert hex_of(style_of(cells, label).color) == PALETTE.muted_text
        number = f"{value:>3}"
        start = text.index(number, text.index(label) + len(label))
        value_ends.add(start + 3)
        assert style_of(cells[start:], number.strip()).bold

        bar = [(c, s) for c, s in cells if c in (FULL, SHADE)]
        assert len(bar) == BAR_WIDTH
        filled = [s for c, s in bar if c == FULL]
        track = [s for c, s in bar if c == SHADE]
        assert len(filled) == filled_cells(value)
        assert row_text(bar) == FULL * len(filled) + SHADE * len(track)
        assert {hex_of(s.color) for s in filled} == {band_colour(value)}
        assert {hex_of(s.color) for s in track} == {PALETTE.bar_track}

    # Right-aligned: every value ends in the same column.
    assert len(value_ends) == 1


async def test_panel_total_row_shows_total_and_rank(all_records, charizards):
    from pokedex_tui.theme import PALETTE

    mega = charizards[1]
    rows, ranks = await run_panel(all_records, mega)
    expected_rank = f"rank #{ranks[mega.key]} of 1215"
    total_line = rows[line_index(rows, expected_rank)]

    assert "634" in row_text(total_line)
    total_style = style_of(total_line, "634")
    assert hex_of(total_style.color) == PALETTE.accent
    assert total_style.bold
    assert hex_of(style_of(total_line, expected_rank).color) == PALETTE.muted_text


async def test_panel_hint_at_the_bottom(all_records, charizards):
    from pokedex_tui.theme import PALETTE

    rows, _ = await run_panel(all_records, charizards[0])
    hint = line_index(rows, "enter: full details")

    assert hint > line_index(rows, "rank #")
    assert hex_of(style_of(rows[hint], "enter").color) == PALETTE.muted_text


async def test_panel_uses_the_raised_background(all_records, charizards):
    from pokedex_tui.theme import PALETTE

    rows, _ = await run_panel(all_records, charizards[0])
    stat_row = rows[line_index(rows, "HP")]

    # Everything except badges and filled bar cells sits on raised.
    plain = [s for c, s in stat_row if c not in (FULL, SHADE)]
    assert {hex_of(s.bgcolor) for s in plain} == {PALETTE.raised}
    assert {hex_of(s.bgcolor) for _, s in rows[0]} == {PALETTE.raised}


async def test_showing_another_pokemon_replaces_everything(all_records, charizards):
    base, mega = charizards
    rows, ranks = await run_panel(all_records, mega, then=base)
    text = "\n".join(row_text(r) for r in rows)

    assert "Mega Charizard X" not in text
    assert "DRAGON" not in text and "FLYING" in text
    assert f"rank #{ranks[base.key]} of 1215" in text
    assert "534" in text and "634" not in text


async def test_panel_with_no_color_keeps_bars_numbers_and_brackets(
    monkeypatch, all_records, charizards
):
    from pokedex_tui.theme import BAR_WIDTH

    monkeypatch.setenv("NO_COLOR", "1")
    base = charizards[0]
    rows, _ = await run_panel(all_records, base)
    text = "\n".join(row_text(r) for r in rows)

    assert "[FIRE]" in text and "[FLYING]" in text
    for label, value in zip(STAT_LABELS, base.stats, strict=True):
        line = row_text(rows[line_index(rows, label)])
        assert f"{value:>3}" in line
        assert sum(line.count(c) for c in (FULL, SHADE)) == BAR_WIDTH


# --- Results table look (C8) -----------------------------------------------------------
#
# These read the real screen at 100 x 30. The first rows of the table are
# Bulbasaur (selected at start), Ivysaur, Venusaur, Mega Venusaur, Charmander.

BADGE_WIDTH = 10


async def table_screen_rows(app):
    """The rendered table rows (inside the table, scrollbar excluded)."""
    table = table_of(app)
    region = table.region
    width = region.width - table.scrollbar_size_vertical
    return [cells[:width] for cells in screen_cells(app, region)]


def runs_with_background(cells, colour):
    """(start, length) of each run of cells whose background is colour."""
    runs, start = [], None
    for x, (_, style) in enumerate([*cells, (" ", None)]):
        inside = style is not None and hex_of(style.bgcolor) == colour
        if inside and start is None:
            start = x
        elif not inside and start is not None:
            runs.append((start, x - start))
            start = None
    return runs


async def test_whole_table_fits_inside_the_results_box():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        usable = table.size.width - table.scrollbar_size_vertical

        assert table.virtual_size.width <= usable
        assert not table.show_horizontal_scrollbar
        rows = await table_screen_rows(app)
        assert row_text(rows[0]).rstrip().endswith("318")  # Bulbasaur's Total


async def test_badges_sit_in_fixed_slots_and_total_lines_up():
    from pokedex_tui.theme import TYPE_STYLES

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        rows = await table_screen_rows(app)
        venusaur, charmander = rows[2], rows[4]

        (grass,) = runs_with_background(venusaur, TYPE_STYLES["Grass"].badge)
        (poison,) = runs_with_background(venusaur, TYPE_STYLES["Poison"].badge)
        (fire,) = runs_with_background(charmander, TYPE_STYLES["Fire"].badge)
        assert grass[1] == poison[1] == fire[1] == BADGE_WIDTH
        assert poison[0] == grass[0] + BADGE_WIDTH + 1  # one space between
        assert fire[0] == grass[0]  # first slot is in the same place

        venusaur_text = row_text(venusaur).rstrip()
        charmander_text = row_text(charmander).rstrip()
        assert venusaur_text.endswith("525") and charmander_text.endswith("309")
        assert len(venusaur_text) == len(charmander_text)


async def test_headings_line_up_with_the_columns_and_have_a_divider():
    from pokedex_tui.theme import PALETTE, TYPE_STYLES
    from pokedex_tui.widgets.box import Box
    from pokedex_tui.widgets.results import Results

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        box = app.screen.query_one(Results).query_one(Box)
        inside = box.content_region
        above = screen_cells(
            app, inside.intersection(inside._replace(height=table.region.y - inside.y))
        )
        heading = next(r for r in above if "Name" in row_text(r))
        divider = above[-1]
        first = (await table_screen_rows(app))[2]  # Venusaur, not selected
        offset = table.region.x - inside.x
        heading_text = row_text(heading)
        first_text = " " * offset + row_text(first)

        # Each heading starts where its column starts.
        assert heading_text.index("#") == first_text.index("0003")
        assert heading_text.index("Name") == first_text.index("Venusaur")
        (grass,) = runs_with_background(first, TYPE_STYLES["Grass"].badge)
        assert heading_text.index("Types") == offset + grass[0]
        # Total is right-aligned over the Total values.
        end = len(first_text.rstrip())
        assert heading_text.rstrip().endswith("Total")
        assert len(heading_text.rstrip()) == end

        for char, style in heading:
            if char.strip():
                assert hex_of(style.color) == PALETTE.muted_text
                assert style.bold
        line = [style for char, style in divider if char == "\u2500"]
        assert len(line) >= end
        assert {hex_of(style.color) for style in line} == {PALETTE.border}


async def test_selected_row_is_white_and_bold_and_badges_keep_colours():
    from pokedex_tui.theme import PALETTE, TYPE_STYLES

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        rows = await table_screen_rows(app)
        selected, other = rows[0], rows[1]
        badges = {
            x
            for name in ("Grass", "Poison")
            for start_at, length in runs_with_background(
                selected, TYPE_STYLES[name].badge
            )
            for x in range(start_at, start_at + length)
        }
        assert len(badges) == 2 * BADGE_WIDTH

        for x, (char, style) in enumerate(selected):
            if x in badges:
                continue
            assert hex_of(style.bgcolor) == PALETTE.selection
            if char.strip():
                assert hex_of(style.color) == PALETTE.selection_text, char
                assert style.bold, char

        text = row_text(selected)
        assert text.lstrip().startswith(">")
        dex_at = row_text(other).index("0002")
        assert hex_of(other[dex_at][1].color) == PALETTE.muted_text


async def test_moving_the_cursor_puts_the_old_row_back_to_muted():
    from pokedex_tui.theme import PALETTE

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("down")
        await pilot.pause()
        rows = await table_screen_rows(app)
        old, new = rows[0], rows[1]

        old_dex = row_text(old).index("0001")
        new_dex = row_text(new).index("0002")
        assert hex_of(old[old_dex][1].color) == PALETTE.muted_text
        assert not old[old_dex][1].bold
        assert hex_of(new[new_dex][1].color) == PALETTE.selection_text


async def test_table_with_no_color_shows_brackets_and_reverse_selected_row(
    monkeypatch,
):
    monkeypatch.setenv("NO_COLOR", "1")
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        assert row(table, 0)[TYPES].split() == ["[GRASS]", "[POISON]"]

        rows = await table_screen_rows(app)
        selected = [style for char, style in rows[0] if char.strip()]
        assert selected and all(style.reverse for style in selected)
        others = [style for char, style in rows[1] if char.strip()]
        assert not any(style.reverse for style in others)
