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


async def test_forms_without_the_species_name_show_both():
    # C10: "Female" alone does not say which Pokemon the row is.
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        names = {row(table, i)[NAME] for i in range(table.row_count)}
        assert {"Nidoran Female", "Nidoran Male", "Castform Sunny Form"} <= names
        assert "Female" not in names


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
        assert sorted(shown) == ["Gen", "Move", "Quit", "Search", "Sort", "Type"]


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

    # C10: the Dex number has a "#" in front, as in main-screen-preview.png.
    assert "#0006 Charizard" in row_text(first)
    assert hex_of(style_of(first, "#0006").color) == PALETTE.muted_text
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


# --- Selection drives the Details pane (C9) ---------------------------------------------


def panel_name_line(app):
    from pokedex_tui.widgets.stats_panel import StatsPanel

    panel = app.screen.query_one(StatsPanel)
    return str(panel.query_one(".name-line").render())


async def test_details_pane_shows_the_first_row_at_startup():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.pause()
        assert panel_name_line(app) == "#0001 Bulbasaur"


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        (["down"], "#0002 Ivysaur"),
        (["down", "down", "up"], "#0002 Ivysaur"),
        (["j", "j"], "#0003 Venusaur"),
        (["end"], "#1025 Pecharunt"),
        (["end", "home"], "#0001 Bulbasaur"),
        (["pagedown", "pageup"], "#0001 Bulbasaur"),
    ],
)
async def test_details_pane_follows_the_cursor(keys, expected):
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        for key in keys:
            await pilot.press(key)
        await pilot.pause()
        assert panel_name_line(app) == expected


async def test_details_pane_follows_each_step_through_the_charmander_line():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        charmander = next(
            i for i in range(table.row_count) if row(table, i)[NAME] == "Charmander"
        )
        for _ in range(charmander):
            await pilot.press("down")
        seen = []
        for _ in range(3):
            await pilot.pause()
            seen.append(panel_name_line(app))
            await pilot.press("down")
        assert seen == ["#0004 Charmander", "#0005 Charmeleon", "#0006 Charizard"]


async def test_details_pane_follows_a_mouse_click():
    from pokedex_tui.widgets.stats_panel import StatsPanel

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        table = table_of(app)
        await pilot.click(table, offset=(10, 3))  # fourth row: Mega Venusaur
        await pilot.pause()
        assert table.cursor_row == 3
        panel = app.screen.query_one(StatsPanel)
        assert panel_name_line(app) == "#0003 Venusaur"
        assert str(panel.query_one(".form-line").render()) == "Mega Venusaur"


async def test_details_pane_shows_the_rank_across_the_whole_pokedex(all_records):
    from pokedex_tui.query import total_ranks
    from pokedex_tui.widgets.stats_panel import StatsPanel

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("down")
        await pilot.pause()
        panel = app.screen.query_one(StatsPanel)
        total_line = str(panel.query_one(".total-row").render())
        ivysaur = next(p for p in all_records if p.name == "Ivysaur")
        rank = total_ranks(all_records)[ivysaur.key]
        assert total_line.endswith(f"rank #{rank} of 1215")


# --- Phase 4: filter and sort state (U1, PTI-9) -------------------------------------
#
# Names these tests expect (rename here if you change them):
# - PokedexApp.criteria: reactive, starts at Criteria().
# - PokedexApp.sort_order: reactive, starts at DEFAULT_SORT.
# - PokedexApp.filtered_records: the current filtered and sorted tuple. Only the
#   app sets it, by calling filter_and_sort, imported into app.py as
#   "from pokedex_tui.query import filter_and_sort".
# - FilterBar.CriteriaChanged(criteria) and FilterBar.SortChanged(sort_order):
#   the messages the filter controls post upward. Each keeps its value in an
#   attribute with the same name as the parameter.


def table_names(app):
    table = table_of(app)
    return [row(table, i)[NAME] for i in range(table.row_count)]


async def test_app_starts_with_default_criteria_and_sort():
    from pokedex_tui.models import DEFAULT_SORT, Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert app.criteria == Criteria()
        assert app.sort_order == DEFAULT_SORT


async def test_filtered_records_start_as_every_record_in_dex_order(all_records):
    from pokedex_tui.query import default_sort_pokemon

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert isinstance(app.filtered_records, tuple)
        assert app.filtered_records == default_sort_pokemon(all_records)
        assert table_of(app).row_count == 1215


async def test_setting_criteria_refills_the_table():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        assert table_of(app).row_count == 151
        assert len(app.filtered_records) == 151
        assert table_names(app)[0] == "Bulbasaur"
        assert table_names(app)[-1] == "Mew"


async def test_table_rows_match_the_filtered_records():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="char")
        await pilot.pause()
        assert table_names(app) == [p.display_name for p in app.filtered_records]


async def test_setting_the_sort_reorders_the_table():
    from pokedex_tui.models import SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.sort_order = SortOrder.for_field("total")
        await pilot.pause()
        assert table_of(app).row_count == 1215
        assert table_names(app)[:2] == ["Eternatus Eternamax", "Mega Mewtwo X"]


async def test_criteria_and_sort_work_together():
    from pokedex_tui.models import Criteria, SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(generations=frozenset({1}))
        app.sort_order = SortOrder.for_field("total")
        await pilot.pause()
        assert table_of(app).row_count == 151
        assert table_names(app)[:3] == ["Mewtwo", "Dragonite", "Mew"]


async def test_going_back_to_default_criteria_shows_every_record():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        app.criteria = Criteria()
        await pilot.pause()
        assert table_of(app).row_count == 1215


async def test_criteria_changed_message_updates_the_app():
    from pokedex_tui.models import Criteria
    from pokedex_tui.widgets.filter_bar import FilterBar

    gen_1 = Criteria(generations=frozenset({1}))
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        bar = app.screen.query_one(FilterBar)
        bar.post_message(FilterBar.CriteriaChanged(gen_1))
        await pilot.pause()
        assert app.criteria == gen_1
        assert table_of(app).row_count == 151


async def test_sort_changed_message_updates_the_app():
    from pokedex_tui.models import SortOrder
    from pokedex_tui.widgets.filter_bar import FilterBar

    by_total = SortOrder.for_field("total")
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        bar = app.screen.query_one(FilterBar)
        bar.post_message(FilterBar.SortChanged(by_total))
        await pilot.pause()
        assert app.sort_order == by_total
        assert table_names(app)[0] == "Eternatus Eternamax"


def test_messages_carry_their_values():
    from pokedex_tui.models import Criteria, SortOrder
    from pokedex_tui.widgets.filter_bar import FilterBar

    criteria = Criteria(search="pika")
    sort_order = SortOrder.for_field("speed")

    assert FilterBar.CriteriaChanged(criteria).criteria == criteria
    assert FilterBar.SortChanged(sort_order).sort_order == sort_order


async def test_an_equal_value_does_not_run_the_query_again(monkeypatch):
    import pokedex_tui.app as app_module
    from pokedex_tui.models import Criteria, SortOrder

    calls = []
    real = app_module.filter_and_sort

    def counting(*args, **kwargs):
        calls.append(args)
        return real(*args, **kwargs)

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        monkeypatch.setattr(app_module, "filter_and_sort", counting)

        # New objects, but equal to the current values.
        app.criteria = Criteria()
        app.sort_order = SortOrder()
        await pilot.pause()
        assert calls == []

        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        assert len(calls) == 1


# --- Phase 4: keep the selection when the list changes (U2, PTI-8) ------------------
#
# Names these tests expect (rename here if you change them):
# - Results.update_records(records) keeps the cursor on the selected record
#   if it is still in the new list, otherwise puts it on the first row.
# - Results.row_positions: dict of record key -> row index, rebuilt on every
#   refill.
# - Results.SelectionCleared(): message posted when a refill leaves no rows.
# - Browser.selected_key: the selected record's key, or None when the list is
#   empty. Set from Results.SelectionChanged and Results.SelectionCleared.
# - StatsPanel.clear_pokemon(): empties every line of the Details pane except
#   the hint line.


async def select_row_by_key(app, pilot, key):
    table = table_of(app)
    table.move_cursor(row=table.get_row_index(key))
    await pilot.pause()


def key_of(all_records, name, form=None):
    return next(p.key for p in all_records if p.name == name and p.form == form)


def _collect_once(keys):
    """Like _collect, but counts each posted message once. The hook sees a
    bubbling message again at every parent it passes through."""
    from pokedex_tui.widgets.results import Results

    seen = {}

    def hook(message):
        if isinstance(message, Results.SelectionChanged) and id(message) not in seen:
            seen[id(message)] = message
            keys.append(message.key)

    return hook


def browser_selected_key(app):
    from typing import cast

    from pokedex_tui.screens.browser import Browser

    return cast(Browser, app.screen).selected_key


def row_is_visible(table, index):
    top = round(table.scroll_y)
    return top <= index < top + table.scrollable_content_region.height


async def test_selection_stays_on_a_record_that_is_still_listed(all_records):
    from pokedex_tui.models import Criteria

    charizard = key_of(all_records, "Charizard")
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await select_row_by_key(app, pilot, charizard)
        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        table = table_of(app)
        assert table.row_count == 151
        assert selected_name(table) == "Charizard"
        assert browser_selected_key(app) == charizard
        assert panel_name_line(app) == "#0006 Charizard"


async def test_kept_selection_is_scrolled_into_view(all_records):
    from pokedex_tui.models import SortOrder

    bulbasaur = key_of(all_records, "Bulbasaur")
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        # Bulbasaur starts on the first row. Sorted by Total it moves far down.
        app.sort_order = SortOrder.for_field("total")
        await pilot.pause()
        table = table_of(app)
        assert browser_selected_key(app) == bulbasaur
        assert selected_name(table) == "Bulbasaur"
        assert table.cursor_row > 100
        assert row_is_visible(table, table.cursor_row)


async def test_marker_is_on_the_kept_row(all_records):
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await select_row_by_key(app, pilot, key_of(all_records, "Charizard"))
        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        table = table_of(app)
        assert marker_rows(table) == [table.cursor_row]


async def test_selection_moves_to_the_first_row_when_its_record_is_gone(all_records):
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await select_row_by_key(app, pilot, key_of(all_records, "Chikorita"))
        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        table = table_of(app)
        assert table.cursor_row == 0
        assert selected_name(table) == "Bulbasaur"
        assert browser_selected_key(app) == key_of(all_records, "Bulbasaur")
        assert panel_name_line(app) == "#0001 Bulbasaur"
        assert marker_rows(table) == [0]


async def test_an_empty_list_clears_the_selection_and_the_details_pane():
    from pokedex_tui.models import Criteria
    from pokedex_tui.widgets.stats_panel import StatsPanel

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="zzzz")
        await pilot.pause()
        assert table_of(app).row_count == 0
        assert browser_selected_key(app) is None
        panel = app.screen.query_one(StatsPanel)
        for line in (".name-line", ".form-line", ".stat-rows", ".total-row"):
            assert str(panel.query_one(line).render()).strip() == "", line
        assert len(panel.query_one(".types-container").children) == 0


async def test_the_list_coming_back_after_empty_selects_the_first_row(all_records):
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="zzzz")
        await pilot.pause()
        app.criteria = Criteria()
        await pilot.pause()
        table = table_of(app)
        assert table.cursor_row == 0
        assert browser_selected_key(app) == key_of(all_records, "Bulbasaur")
        assert panel_name_line(app) == "#0001 Bulbasaur"


async def test_a_refill_posts_selection_changed_once_with_the_kept_key(all_records):
    from pokedex_tui.models import Criteria

    charizard = key_of(all_records, "Charizard")
    keys = []
    app = make_app()
    async with app.run_test(size=SIZE, message_hook=_collect_once(keys)) as pilot:
        await start(app, pilot)
        await select_row_by_key(app, pilot, charizard)
        keys.clear()
        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        assert keys == [charizard]


async def test_a_refill_to_the_first_row_posts_selection_changed_once(all_records):
    from pokedex_tui.models import Criteria

    keys = []
    app = make_app()
    async with app.run_test(size=SIZE, message_hook=_collect_once(keys)) as pilot:
        await start(app, pilot)
        await select_row_by_key(app, pilot, key_of(all_records, "Chikorita"))
        keys.clear()
        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        assert keys == [key_of(all_records, "Bulbasaur")]


async def test_row_positions_match_the_new_rows():
    from pokedex_tui.models import Criteria
    from pokedex_tui.widgets.results import Results

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="char")
        await pilot.pause()
        positions = app.screen.query_one(Results).row_positions
        assert positions == {
            p.key: index for index, p in enumerate(app.filtered_records)
        }


# --- Phase 4: live match count and empty state (U3, PTI-7) --------------------------
#
# Names these tests expect (rename here if you change them):
# - PokedexHeader.set_header_match_count(n), called from the same app method
#   that refills the table, with the length of filtered_records.
# - Results has a Static with id "empty-message", hidden while there are rows.
#   When the list is empty it is shown, and the ".headings" line and the
#   DataTable are hidden.

EMPTY_MESSAGE = "No Pokémon match these filters. Press r to reset."


def empty_message(app):
    return app.screen.query_one("#empty-message")


def headings(app):
    return app.screen.query_one(".headings")


async def test_count_follows_the_filtered_list():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        assert count_text(app) == "151 of 1215"


async def test_count_shows_zero_when_nothing_matches():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="zzzz")
        await pilot.pause()
        assert count_text(app) == "0 of 1215"


async def test_count_goes_back_to_the_full_number():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        app.criteria = Criteria()
        await pilot.pause()
        assert count_text(app) == "1215 of 1215"


async def test_count_total_is_the_number_of_loaded_records(small_csv):
    from pokedex_tui.models import Criteria

    app = make_app(small_csv)
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="zzzz")
        await pilot.pause()
        assert count_text(app) == "0 of 14"


async def test_count_does_not_change_when_only_the_sort_changes():
    from pokedex_tui.models import Criteria, SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(generations=frozenset({1}))
        app.sort_order = SortOrder.for_field("total")
        await pilot.pause()
        assert count_text(app) == "151 of 1215"


async def test_empty_message_is_hidden_while_there_are_rows():
    from textual.widgets import DataTable

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert not empty_message(app).display
        assert headings(app).display
        assert app.screen.query_one(DataTable).display


async def test_empty_list_shows_the_message_instead_of_the_table():
    from textual.widgets import DataTable

    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="zzzz")
        await pilot.pause()
        assert empty_message(app).display
        assert str(empty_message(app).render()) == EMPTY_MESSAGE
        assert not headings(app).display
        assert not app.screen.query_one(DataTable).display


async def test_empty_message_is_centred_and_muted():
    from pokedex_tui.models import Criteria
    from pokedex_tui.theme import PALETTE

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="zzzz")
        await pilot.pause()
        message = empty_message(app)
        rows = screen_cells(app, message.content_region)
        line = next(cells for cells in rows if row_text(cells).strip())
        text = row_text(line)
        assert text.strip() == EMPTY_MESSAGE
        left = len(text) - len(text.lstrip())
        right = len(text) - len(text.rstrip())
        assert abs(left - right) <= 1, (left, right)
        letters = [style for char, style in line if not char.isspace()]
        assert {hex_of(style.color) for style in letters} == {PALETTE.muted_text}


async def test_table_comes_back_when_there_are_results_again(all_records):
    from textual.widgets import DataTable

    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="zzzz")
        await pilot.pause()
        app.criteria = Criteria(search="char")
        await pilot.pause()
        table = app.screen.query_one(DataTable)
        assert table.display
        assert headings(app).display
        assert not empty_message(app).display
        assert table.row_count == 9
        assert table.cursor_row == 0
        assert browser_selected_key(app) == key_of(all_records, "Charmander")
        assert app.focused is table


# --- Phase 4: filter bar layout and focus styling (U4, PTI-6) -----------------------
#
# Names these tests expect (rename here if you change them):
# - FilterBar holds five Box widgets, left to right, with these ids and titles:
#   "search-bar" Search, "type-filter" Type, "type-2-filter" and Type,
#   "gen-filter" Gen, "sort" Sort.
# - Each box holds something that can take focus, so Tab stops once per box.
#   The tests only ask which box holds the focused widget, so U5 to U8 can
#   swap the placeholder for the real control without changing these tests.
# - Placeholder values until U5 to U8: Search empty, Type "Any", and Type
#   "Any", Gen "All" (each with a "▼" at the right edge), Sort
#   "Dex # ascending".

FILTER_BOXES = (
    ("search-bar", "Search"),
    ("type-filter", "Type"),
    ("type-2-filter", "and Type"),
    ("gen-filter", "Gen"),
    ("sort", "Sort"),
)


def filter_box(app, box_id):
    return app.screen.query_one(f"#{box_id}")


def focused_place(app):
    """The id of the filter box holding the focus, or "table" for the table."""
    from textual.widgets import DataTable

    widget = app.focused
    if isinstance(widget, DataTable):
        return "table"
    ids = {box_id for box_id, _ in FILTER_BOXES}
    while widget is not None:
        if widget.id in ids:
            return widget.id
        widget = widget.parent
    return None


def box_value_text(app, box_id):
    """The first line inside the box's border, as drawn on screen."""
    region = filter_box(app, box_id).content_region
    return row_text(screen_cells(app, region)[0])


def box_border_colours(app, box_id, title):
    """(title colours, top border line colours) as drawn on screen."""
    top = screen_cells(app, filter_box(app, box_id).region)[0]
    text = row_text(top)
    start_at = text.index(title)
    title_cells = top[start_at : start_at + len(title)]
    line_cells = [style for char, style in top if char == "─"]
    return (
        {hex_of(s.color) for _, s in title_cells},
        {hex_of(s.color) for s in line_cells},
    )


async def test_filter_bar_has_five_boxes_in_order():
    from pokedex_tui.widgets.box import Box
    from pokedex_tui.widgets.filter_bar import FilterBar

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        boxes = list(app.screen.query_one(FilterBar).query_children(Box))
        assert [(b.id, b.border_title) for b in boxes] == list(FILTER_BOXES)
        xs = [b.region.x for b in boxes]
        assert xs == sorted(xs)
        assert {b.region.y for b in boxes} == {1}
        assert {b.region.height for b in boxes} == {3}


async def test_search_box_is_the_widest_at_30_columns():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        widths = {
            box_id: filter_box(app, box_id).region.width for box_id, _ in FILTER_BOXES
        }
        assert widths["search-bar"] == 30
        assert all(w < 30 for box_id, w in widths.items() if box_id != "search-bar")


async def test_filter_bar_is_on_the_surface_background():
    from pokedex_tui.theme import PALETTE
    from pokedex_tui.widgets.filter_bar import FilterBar

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        rows = screen_cells(app, app.screen.query_one(FilterBar).region)
        backgrounds = {hex_of(style.bgcolor) for row in rows for _, style in row}
        assert backgrounds == {PALETTE.surface}


@pytest.mark.parametrize(
    ("box_id", "value"),
    [("type-filter", "Any"), ("type-2-filter", "Any"), ("gen-filter", "All")],
)
async def test_dropdown_boxes_show_a_value_and_a_down_arrow(box_id, value):
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        text = box_value_text(app, box_id)
        assert text.strip().startswith(value)
        assert text.rstrip().endswith("▼")
        # The arrow sits at the right edge (one space of padding allowed).
        assert len(text) - len(text.rstrip()) <= 1


async def test_sort_box_shows_the_sort_in_words():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert box_value_text(app, "sort").split()[:3] == ["Dex", "#", "ascending"]


async def test_search_box_starts_with_no_search_text():
    # U5 swaps the placeholder for an Input, which shows "name or form"
    # until the user types.
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert box_value_text(app, "search-bar").strip() in ("", "name or form")
        assert app.criteria.search == ""


async def test_tab_moves_through_the_boxes_then_the_table():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert focused_place(app) == "table"
        visited = []
        for _ in range(6):
            await pilot.press("tab")
            await pilot.pause()
            visited.append(focused_place(app))
        assert visited == [box_id for box_id, _ in FILTER_BOXES] + ["table"]


async def test_shift_tab_goes_the_other_way():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        visited = []
        for _ in range(6):
            await pilot.press("shift+tab")
            await pilot.pause()
            visited.append(focused_place(app))
        assert visited == [box_id for box_id, _ in reversed(FILTER_BOXES)] + ["table"]


async def test_only_the_focused_filter_box_has_an_accent_border():
    from pokedex_tui.theme import PALETTE

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        for focused_id, _ in FILTER_BOXES:
            await pilot.press("tab")
            await pilot.pause()
            assert focused_place(app) == focused_id
            for box_id, title in FILTER_BOXES:
                titles, lines = box_border_colours(app, box_id, title)
                if box_id == focused_id:
                    assert (titles, lines) == ({PALETTE.accent}, {PALETTE.accent})
                else:
                    assert (titles, lines) == ({PALETTE.muted_text}, {PALETTE.border})


# --- Phase 4: live search box (U5, PTI-5) -------------------------------------------
#
# Names these tests expect (rename here if you change them):
# - An Input with id "search-input" inside the "search-bar" box, placeholder
#   "name or form".
# - SEARCH_DEBOUNCE in pokedex_tui.widgets.filter_bar: the wait in seconds
#   after the last key before FilterBar posts CriteriaChanged. It must be read
#   when the timer is started (not copied at import), so a test can change it.
# - "/" focuses the search box, Escape and Enter in it focus the table.

SEARCH_WAIT = 0.4  # longer than the debounce, so the search has been sent


def search_input(app):
    from textual.widgets import Input

    return app.screen.query_one("#search-input", Input)


def _collect_criteria(found):
    """Each CriteriaChanged posted by the filter bar, counted once."""
    from pokedex_tui.widgets.filter_bar import FilterBar

    seen = {}

    def hook(message):
        if isinstance(message, FilterBar.CriteriaChanged) and id(message) not in seen:
            seen[id(message)] = message
            found.append(message.criteria)

    return hook


async def type_text(pilot, text):
    for char in text:
        await pilot.press(char)


async def test_search_box_is_an_input_with_a_placeholder():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        box = filter_box(app, "search-bar")
        field = search_input(app)
        assert field.parent is box
        assert field.placeholder == "name or form"
        assert field.value == ""


async def test_slash_focuses_the_search_box_from_the_table():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash")
        await pilot.pause()
        assert app.focused is search_input(app)


async def test_slash_focuses_the_search_box_from_another_box():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("tab", "tab")  # Search, then Type
        await pilot.pause()
        assert focused_place(app) == "type-filter"
        await pilot.press("slash")
        await pilot.pause()
        assert app.focused is search_input(app)


async def test_typing_narrows_the_table():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash")
        await type_text(pilot, "char")
        await pilot.pause(SEARCH_WAIT)
        assert app.criteria.search == "char"
        assert table_of(app).row_count == 9
        assert count_text(app) == "9 of 1215"


async def test_typing_keeps_the_focus_in_the_search_box():
    # Each refill must not pull the focus into the table.
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash")
        await type_text(pilot, "ch")
        await pilot.pause(SEARCH_WAIT)
        await type_text(pilot, "ar")
        await pilot.pause(SEARCH_WAIT)
        assert app.focused is search_input(app)
        assert search_input(app).value == "char"


async def test_search_without_accents_finds_flabebe():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash")
        await type_text(pilot, "flabebe")
        await pilot.pause(SEARCH_WAIT)
        assert "Flabébé" in table_names(app)


async def test_search_keeps_the_other_criteria():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(generations=frozenset({1}), type1="Fire")
        await pilot.pause()
        await pilot.press("slash")
        await type_text(pilot, "char")
        await pilot.pause(SEARCH_WAIT)
        assert app.criteria == Criteria(
            search="char", generations=frozenset({1}), type1="Fire"
        )


async def test_fast_typing_sends_one_search(monkeypatch):
    from pokedex_tui.widgets import filter_bar

    # A long wait, so the four keys always land inside it.
    monkeypatch.setattr(filter_bar, "SEARCH_DEBOUNCE", 0.5)
    found = []
    app = make_app()
    async with app.run_test(size=SIZE, message_hook=_collect_criteria(found)) as pilot:
        await start(app, pilot)
        await pilot.press("slash")
        await type_text(pilot, "char")
        await pilot.pause()
        assert found == [], "sent before the wait was over"
        await pilot.pause(0.8)
        assert [c.search for c in found] == ["char"]


async def test_debounce_is_between_100_and_150_ms():
    from pokedex_tui.widgets.filter_bar import SEARCH_DEBOUNCE

    assert 0.1 <= SEARCH_DEBOUNCE <= 0.15


async def test_clearing_the_search_shows_every_record_again():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash")
        await type_text(pilot, "char")
        await pilot.pause(SEARCH_WAIT)
        await pilot.press(*["backspace"] * 4)
        await pilot.pause(SEARCH_WAIT)
        assert app.criteria.search == ""
        assert table_of(app).row_count == 1215


async def test_escape_goes_to_the_table_and_keeps_the_text():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash")
        await type_text(pilot, "char")
        await pilot.press("escape")
        await pilot.pause(SEARCH_WAIT)
        assert focused_place(app) == "table"
        assert search_input(app).value == "char"
        assert app.criteria.search == "char"


async def test_enter_goes_to_the_table():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash")
        await type_text(pilot, "char")
        await pilot.press("enter")
        await pilot.pause(SEARCH_WAIT)
        assert focused_place(app) == "table"
        assert app.criteria.search == "char"
        assert selected_name(table_of(app)) == "Charmander"


async def test_letter_keys_type_into_the_search_box():
    """Design doc 5: no single-letter key fires while the user is typing."""
    from pokedex_tui.models import DEFAULT_SORT

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash")
        await type_text(pilot, "GengartTgsSrq19")
        await pilot.pause(SEARCH_WAIT)
        assert app.is_running
        assert app.focused is search_input(app)
        assert search_input(app).value == "GengartTgsSrq19"
        assert app.criteria.type1 is None
        assert app.criteria.type2 is None
        assert app.criteria.generations == frozenset()
        assert app.sort_order == DEFAULT_SORT


# --- Phase 4: the two type pickers (U6, PTI-4) --------------------------------------
#
# Names these tests expect (rename here if you change them):
# - A Select with id "type-1-select" in the "type-filter" box and one with id
#   "type-2-select" in the "type-2-filter" box, each with allow_blank=False.
# - Options in query.type_options(slot) order. Labels: "Any" first, then for
#   the second picker "None (n)", then "Type (n)" with the match count from
#   query.type_counts. "Any" sets the criteria value to None, "None" to
#   NO_SECOND_TYPE.
# - "t" opens the first picker and "T" the second (focus moves to it and its
#   list is open). Counts are refreshed each time a picker opens.
# - Options with a count of 0 are drawn in the muted colour and can still be
#   chosen.


def type_select(app, slot):
    from textual.widgets import Select

    return app.screen.query_one(f"#type-{slot}-select", Select)


def open_option_labels(app, slot):
    """The labels of the open picker's list, as plain text."""
    from textual.widgets import OptionList

    options = type_select(app, slot).query_one(OptionList)
    return [
        str(options.get_option_at_index(i).prompt) for i in range(options.option_count)
    ]


async def choose_type(pilot, key, label):
    """Open a picker with its key and pick the option whose label starts with label."""
    app = pilot.app
    slot = 1 if key == "t" else 2
    await pilot.press(key)
    await pilot.pause()
    labels = open_option_labels(app, slot)
    target = next(i for i, text in enumerate(labels) if text.split(" (")[0] == label)
    from textual.widgets import OptionList

    current = type_select(app, slot).query_one(OptionList).highlighted or 0
    step = "down" if target >= current else "up"
    await pilot.press(*[step] * abs(target - current))
    await pilot.press("enter")
    await pilot.pause()


async def test_type_pickers_sit_in_the_type_boxes():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert type_select(app, 1).parent is filter_box(app, "type-filter")
        assert type_select(app, 2).parent is filter_box(app, "type-2-filter")


async def test_t_opens_the_first_picker():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("t")
        await pilot.pause()
        assert type_select(app, 1).expanded
        assert focused_place(app) == "type-filter"
        assert not type_select(app, 2).expanded


async def test_shift_t_opens_the_second_picker():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("T")
        await pilot.pause()
        assert type_select(app, 2).expanded
        assert focused_place(app) == "type-2-filter"
        assert not type_select(app, 1).expanded


async def test_first_picker_options_are_any_then_the_types_with_counts(all_records):
    from pokedex_tui.models import TYPES, Criteria
    from pokedex_tui.query import type_counts

    counts = type_counts(all_records, Criteria(), 1)
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("t")
        await pilot.pause()
        assert open_option_labels(app, 1) == ["Any"] + [
            f"{name} ({counts[name]})" for name in TYPES
        ]


async def test_second_picker_adds_none_after_any(all_records):
    from pokedex_tui.models import NO_SECOND_TYPE, TYPES, Criteria
    from pokedex_tui.query import type_counts

    counts = type_counts(all_records, Criteria(), 2)
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("T")
        await pilot.pause()
        assert open_option_labels(app, 2) == [
            "Any",
            f"None ({counts[NO_SECOND_TYPE]})",
        ] + [f"{name} ({counts[name]})" for name in TYPES]


async def test_choosing_water_matches_either_slot():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await choose_type(pilot, "t", "Water")
        assert app.criteria.type1 == "Water"
        assert app.criteria.type2 is None
        found = app.filtered_records
        assert found and all("Water" in p.types for p in found)
        assert any(p.type2 == "Water" for p in found)


async def test_water_and_flying_match_in_either_order():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await choose_type(pilot, "t", "Water")
        await choose_type(pilot, "T", "Flying")
        assert (app.criteria.type1, app.criteria.type2) == ("Water", "Flying")
        pairs = {(p.type1, p.type2) for p in app.filtered_records}
        assert pairs == {("Water", "Flying"), ("Flying", "Water")}


async def test_fire_and_none_gives_37_pure_fire_types():
    from pokedex_tui.models import NO_SECOND_TYPE

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await choose_type(pilot, "t", "Fire")
        await choose_type(pilot, "T", "None")
        assert app.criteria.type2 == NO_SECOND_TYPE
        assert table_of(app).row_count == 37
        assert count_text(app) == "37 of 1215"


async def test_choosing_any_clears_the_slot():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await choose_type(pilot, "t", "Fire")
        await choose_type(pilot, "t", "Any")
        assert app.criteria.type1 is None
        assert table_of(app).row_count == 1215


async def test_choosing_a_type_keeps_the_other_criteria():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="char", generations=frozenset({1}))
        await pilot.pause()
        await choose_type(pilot, "t", "Fire")
        assert app.criteria == Criteria(
            search="char", generations=frozenset({1}), type1="Fire"
        )


async def test_counts_are_refreshed_when_a_picker_opens(all_records):
    from pokedex_tui.models import Criteria
    from pokedex_tui.query import type_counts

    gen_1 = Criteria(generations=frozenset({1}))
    counts = type_counts(all_records, gen_1, 1)
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = gen_1
        await pilot.pause()
        await pilot.press("t")
        await pilot.pause()
        labels = open_option_labels(app, 1)
        assert "Dark (0)" in labels
        assert f"Fire ({counts['Fire']})" in labels


async def test_zero_count_types_are_muted_but_can_be_chosen():
    from pokedex_tui.models import Criteria
    from pokedex_tui.theme import PALETTE

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(generations=frozenset({1}))
        await pilot.pause()
        await pilot.press("t")
        await pilot.pause()
        rows = screen_cells(app, app.screen.region)
        line = next(cells for cells in rows if "Dark (0)" in row_text(cells))
        text = row_text(line)
        at = text.index("Dark (0)")
        letters = [s for c, s in line[at : at + len("Dark (0)")] if not c.isspace()]
        assert {hex_of(s.color) for s in letters} == {PALETTE.muted_text}

        await pilot.press("escape")
        await pilot.pause()
        await choose_type(pilot, "t", "Dark")
        assert app.criteria.type1 == "Dark"
        assert table_of(app).row_count == 0


async def test_type_keys_do_nothing_while_typing_in_search():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash", "t", "T")
        await pilot.pause()
        assert not type_select(app, 1).expanded
        assert not type_select(app, 2).expanded
        assert search_input(app).value == "tT"


# --- Phase 4: generation picker and quick keys (U7, PTI-3) -----------------------------
#
# Names these tests expect (rename here if you change them):
# - A Select with id "gen-select" in the "gen-filter" box, with allow_blank=False.
# - Options in query.generation_options() order, labelled "All", then "1" to "9"
#   (no counts). "All" sets criteria.generations to an empty frozenset; a number
#   sets a frozenset holding just that number.
# - "g" opens the picker (focus moves to it and its list is open). The footer
#   shows "Gen".
# - Keys "1" to "9" work only while the table has focus, and are hidden from the
#   footer. A number sets that generation; the same number again clears it.
# - The Gen box always shows the generation in app.criteria, however it was set.


def gen_select(app):
    from textual.widgets import Select

    return app.screen.query_one("#gen-select", Select)


def open_gen_labels(app):
    """The labels of the open Gen picker's list, as plain text."""
    from textual.widgets import OptionList

    options = gen_select(app).query_one(OptionList)
    return [
        str(options.get_option_at_index(i).prompt) for i in range(options.option_count)
    ]


async def choose_gen(pilot, label):
    """Open the Gen picker with "g" and pick the option with this label."""
    from textual.widgets import OptionList

    app = pilot.app
    await pilot.press("g")
    await pilot.pause()
    target = open_gen_labels(app).index(label)
    current = gen_select(app).query_one(OptionList).highlighted or 0
    step = "down" if target >= current else "up"
    await pilot.press(*[step] * abs(target - current))
    await pilot.press("enter")
    await pilot.pause()


async def focus_table(app, pilot):
    table_of(app).focus()
    await pilot.pause()


async def test_gen_picker_sits_in_the_gen_box():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert gen_select(app).parent is filter_box(app, "gen-filter")


async def test_g_opens_the_gen_picker():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("g")
        await pilot.pause()
        assert gen_select(app).expanded
        assert focused_place(app) == "gen-filter"


async def test_gen_options_are_all_then_1_to_9():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("g")
        await pilot.pause()
        assert open_gen_labels(app) == ["All"] + [str(n) for n in range(1, 10)]


async def test_choosing_gen_3_shows_only_gen_3_rows():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await choose_gen(pilot, "3")
        assert app.criteria.generations == frozenset({3})
        assert table_of(app).row_count == 141
        assert {p.generation for p in app.filtered_records} == {3}


async def test_choosing_all_clears_the_generation():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await choose_gen(pilot, "3")
        await choose_gen(pilot, "All")
        assert app.criteria.generations == frozenset()
        assert table_of(app).row_count == 1215


async def test_choosing_a_gen_keeps_the_other_criteria():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(search="char", type1="Fire")
        await pilot.pause()
        await choose_gen(pilot, "1")
        assert app.criteria == Criteria(
            search="char", type1="Fire", generations=frozenset({1})
        )


async def test_number_key_on_the_table_sets_that_generation():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await focus_table(app, pilot)
        await pilot.press("1")
        await pilot.pause()
        assert app.criteria.generations == frozenset({1})
        assert table_of(app).row_count == 151


async def test_same_number_key_again_goes_back_to_all():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await focus_table(app, pilot)
        await pilot.press("1")
        await pilot.pause()
        await pilot.press("1")
        await pilot.pause()
        assert app.criteria.generations == frozenset()
        assert table_of(app).row_count == 1215


async def test_a_different_number_key_switches_the_generation():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await focus_table(app, pilot)
        await pilot.press("1")
        await pilot.pause()
        await pilot.press("9")
        await pilot.pause()
        assert app.criteria.generations == frozenset({9})
        assert table_of(app).row_count == 140


async def test_number_key_keeps_the_other_criteria():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(type1="Fire")
        await pilot.pause()
        await focus_table(app, pilot)
        await pilot.press("1")
        await pilot.pause()
        assert app.criteria == Criteria(type1="Fire", generations=frozenset({1}))
        assert table_of(app).row_count == 12


async def test_number_key_updates_the_gen_box():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await focus_table(app, pilot)
        await pilot.press("4")
        await pilot.pause()
        assert box_value_text(app, "gen-filter").strip().startswith("4")
        await pilot.press("4")
        await pilot.pause()
        assert box_value_text(app, "gen-filter").strip().startswith("All")


async def test_gen_box_follows_the_app_criteria():
    from pokedex_tui.models import Criteria

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.criteria = Criteria(generations=frozenset({6}))
        await pilot.pause()
        assert box_value_text(app, "gen-filter").strip().startswith("6")


async def test_number_keys_type_into_the_search_box():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash", "1", "g")
        await pilot.pause(SEARCH_WAIT)
        assert search_input(app).value == "1g"
        assert app.criteria.generations == frozenset()
        assert not gen_select(app).expanded


async def test_gen_picker_sends_no_change_on_start():
    found = []
    app = make_app()
    async with app.run_test(size=SIZE, message_hook=_collect_criteria(found)) as pilot:
        await start(app, pilot)
        await pilot.pause()
        assert found == []


# --- Phase 4: sorting controls (U8, PTI-2) ---------------------------------------------
#
# Names these tests expect (rename here if you change them):
# - "s" moves app.sort_order to sort_order.next_field() and "S" to
#   sort_order.flipped(). The footer shows "Sort" ("S" is hidden). Neither key
#   does anything while typing in the search box.
# - A Select with id "sort-select" in the "sort" box, allow_blank=False, with one
#   option per field in SORT_FIELDS order. Each option's label starts with the
#   field's words below. Picking a field sets SortOrder.for_field(field).
# - The Sort box shows "<words> ascending" or "<words> descending", and always
#   follows app.sort_order, however it was set. The Select sends no SortChanged
#   when it mounts.
# - Clicking a heading in the ".headings" line sorts by that column: "#" is
#   "dex", "Name" is "name", "Total" is "total". Clicking the active heading
#   again flips the direction. "Types" can't be sorted, so clicking it does
#   nothing.
# - The headings line shows one "▲" (ascending) or "▼" (descending) inside the
#   active column, or none when the sort field has no column (HP to Spe).

SORT_WORDS = {
    "dex": "Dex #",
    "name": "Name",
    "total": "Total",
    "hp": "HP",
    "attack": "Atk",
    "defense": "Def",
    "sp_atk": "SpA",
    "sp_def": "SpD",
    "speed": "Spe",
}

# Heading text for each sortable column key in results.COLUMNS.
SORT_HEADINGS = {"dex_id": "#", "name": "Name", "total": "Total"}


def sort_select(app):
    from textual.widgets import Select

    return app.screen.query_one("#sort-select", Select)


def sort_box_words(app):
    """The Sort box's shown value, without the dropdown arrow."""
    return " ".join(box_value_text(app, "sort").replace("▼", "").split())


def headings_text(app):
    region = app.screen.query_one(".headings").region
    return row_text(screen_cells(app, region)[0])


def heading_span(key):
    """Where a column's heading sits in the headings line, padding included."""
    from pokedex_tui.widgets.results import CELL_PADDING, COLUMNS

    start = 0
    for column_key, _, width, _ in COLUMNS:
        end = start + width + 2 * CELL_PADDING
        if column_key == key:
            return range(start, end)
        start = end
    raise KeyError(key)


def arrows(app):
    """(position, arrow) for every sort arrow in the headings line."""
    return [(i, c) for i, c in enumerate(headings_text(app)) if c in "▲▼"]


async def click_heading(pilot, word):
    app = pilot.app
    text = headings_text(app)
    span = heading_span(next(k for k, v in SORT_HEADINGS.items() if v == word))
    x = text.index(word, span.start)
    await pilot.click(".headings", offset=(x, 0))
    await pilot.pause()


async def choose_sort(pilot, field):
    """Focus the Sort dropdown, open it and pick this field."""
    from textual.widgets import OptionList

    app = pilot.app
    sort_select(app).focus()
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()
    options = sort_select(app).query_one(OptionList)
    labels = [
        str(options.get_option_at_index(i).prompt) for i in range(options.option_count)
    ]
    words = SORT_WORDS[field]
    target = next(
        i
        for i, text in enumerate(labels)
        if text == words or text.startswith(words + " ")
    )
    current = options.highlighted or 0
    step = "down" if target >= current else "up"
    await pilot.press(*[step] * abs(target - current))
    await pilot.press("enter")
    await pilot.pause()


def _collect_sorts(found):
    """Each SortChanged posted by the filter bar, counted once."""
    from pokedex_tui.widgets.filter_bar import FilterBar

    seen = {}

    def hook(message):
        if isinstance(message, FilterBar.SortChanged) and id(message) not in seen:
            seen[id(message)] = message
            found.append(message.sort_order)

    return hook


async def test_s_moves_to_the_next_sort_field():
    from pokedex_tui.models import SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("s")
        await pilot.pause()
        assert app.sort_order == SortOrder.for_field("name")


async def test_s_twice_sorts_by_total_highest_first():
    from pokedex_tui.models import SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("s", "s")
        await pilot.pause()
        assert app.sort_order == SortOrder(by="total", descending=True)
        totals = [p.total for p in app.filtered_records]
        assert totals == sorted(totals, reverse=True)
        names = [p.display_name for p in app.filtered_records]
        assert names[0] == "Eternatus Eternamax"


async def test_s_wraps_back_to_dex_after_speed():
    from pokedex_tui.models import DEFAULT_SORT, SORT_FIELDS

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press(*["s"] * len(SORT_FIELDS))
        await pilot.pause()
        assert app.sort_order == DEFAULT_SORT


async def test_shift_s_flips_the_direction():
    from pokedex_tui.models import SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("s", "s", "S")
        await pilot.pause()
        assert app.sort_order == SortOrder(by="total", descending=False)
        totals = [p.total for p in app.filtered_records]
        assert totals == sorted(totals)


async def test_sort_keys_type_into_the_search_box():
    from pokedex_tui.models import DEFAULT_SORT

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press("slash", "s", "S")
        await pilot.pause(SEARCH_WAIT)
        assert search_input(app).value == "sS"
        assert app.sort_order == DEFAULT_SORT


async def test_sort_box_starts_as_dex_ascending():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        assert sort_select(app).parent is filter_box(app, "sort")
        assert sort_box_words(app) == "Dex # ascending"


@pytest.mark.parametrize(
    ("keys", "words"),
    [
        (["s"], "Name ascending"),
        (["s", "s"], "Total descending"),
        (["s", "s", "S"], "Total ascending"),
        (["s", "s", "s"], "HP descending"),
    ],
)
async def test_sort_box_shows_each_sort_in_words(keys, words):
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await pilot.press(*keys)
        await pilot.pause()
        assert sort_box_words(app) == words


async def test_sort_box_follows_the_app_sort_order():
    from pokedex_tui.models import SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.sort_order = SortOrder.for_field("speed")
        await pilot.pause()
        assert sort_box_words(app) == "Spe descending"


async def test_sort_dropdown_lists_the_nine_fields_in_order():
    from textual.widgets import OptionList

    from pokedex_tui.models import SORT_FIELDS

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        sort_select(app).focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert sort_select(app).expanded
        options = sort_select(app).query_one(OptionList)
        labels = [
            str(options.get_option_at_index(i).prompt)
            for i in range(options.option_count)
        ]
        assert len(labels) == len(SORT_FIELDS)
        for label, field in zip(labels, SORT_FIELDS, strict=True):
            words = SORT_WORDS[field]
            assert label == words or label.startswith(words + " ")


async def test_picking_a_field_in_the_dropdown_sorts_by_it():
    from pokedex_tui.models import SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await choose_sort(pilot, "hp")
        assert app.sort_order == SortOrder.for_field("hp")
        assert sort_box_words(app) == "HP descending"


async def test_sort_dropdown_sends_no_change_on_start():
    found = []
    app = make_app()
    async with app.run_test(size=SIZE, message_hook=_collect_sorts(found)) as pilot:
        await start(app, pilot)
        await pilot.pause()
        assert found == []


async def test_clicking_name_sorts_a_to_z_then_z_to_a():
    from pokedex_tui.models import SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await click_heading(pilot, "Name")
        assert app.sort_order == SortOrder(by="name", descending=False)
        await click_heading(pilot, "Name")
        assert app.sort_order == SortOrder(by="name", descending=True)


async def test_clicking_total_sorts_highest_first():
    from pokedex_tui.models import SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await click_heading(pilot, "Total")
        assert app.sort_order == SortOrder(by="total", descending=True)


async def test_clicking_the_active_dex_heading_flips_it():
    from pokedex_tui.models import SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await click_heading(pilot, "#")
        assert app.sort_order == SortOrder(by="dex", descending=True)


async def test_clicking_types_does_not_change_the_sort():
    from pokedex_tui.models import DEFAULT_SORT

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        x = headings_text(app).index("Types")
        await pilot.click(".headings", offset=(x, 0))
        await pilot.pause()
        assert app.sort_order == DEFAULT_SORT


async def test_dex_heading_shows_an_up_arrow_at_start():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        ((at, arrow),) = arrows(app)
        assert arrow == "▲"
        assert at in heading_span("dex_id")


async def test_arrow_follows_the_active_column():
    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        await click_heading(pilot, "Name")
        ((at, arrow),) = arrows(app)
        assert (arrow, at in heading_span("name")) == ("▲", True)
        await click_heading(pilot, "Name")
        ((at, arrow),) = arrows(app)
        assert (arrow, at in heading_span("name")) == ("▼", True)
        await click_heading(pilot, "Total")
        ((at, arrow),) = arrows(app)
        assert (arrow, at in heading_span("total")) == ("▼", True)
        assert "Name" in headings_text(app) and "Total" in headings_text(app)


async def test_no_arrow_when_the_sort_has_no_column():
    from pokedex_tui.models import SortOrder

    app = make_app()
    async with app.run_test(size=SIZE) as pilot:
        await start(app, pilot)
        app.sort_order = SortOrder.for_field("hp")
        await pilot.pause()
        assert arrows(app) == []
