"""PTI-100: the default record order lives in query.py, and the App keeps a tuple.

Names these tests expect (rename here if you chose different ones):
- pokedex_tui.query.default_sort_pokemon(records): takes any iterable of
  Pokemon and returns a new tuple in Dex order, base form before its forms.
- PokedexApp.all_records: that tuple, stored once the data has loaded.
"""

import subprocess
import sys

# --- default_sort_pokemon ---------------------------------------------------------


def test_default_order_starts_with_the_venusaur_line(all_records):
    from pokedex_tui.query import default_sort_pokemon

    first = default_sort_pokemon(all_records)[:4]

    assert [(p.name, p.form) for p in first] == [
        ("Bulbasaur", None),
        ("Ivysaur", None),
        ("Venusaur", None),
        ("Venusaur", "Mega Venusaur"),
    ]


def test_default_order_returns_a_tuple(all_records):
    from pokedex_tui.query import default_sort_pokemon

    assert isinstance(default_sort_pokemon(all_records), tuple)


def test_default_order_is_dex_order_with_base_form_first(all_records):
    from pokedex_tui.query import default_sort_pokemon

    ordered = default_sort_pokemon(all_records)

    keys = [(p.dex_id, p.is_form) for p in ordered]
    assert keys == sorted(keys)
    assert len(ordered) == len(all_records)


def test_default_order_accepts_any_iterable_and_leaves_input_alone(all_records):
    from pokedex_tui.query import default_sort_pokemon

    backwards = list(reversed(all_records))
    before = list(backwards)

    ordered = default_sort_pokemon(iter(backwards))

    assert backwards == before
    assert len(ordered) == len(backwards)
    assert [p.name for p in ordered[:3]] == ["Bulbasaur", "Ivysaur", "Venusaur"]


def test_forms_of_one_pokemon_keep_csv_order(all_records):
    from pokedex_tui.query import default_sort_pokemon

    megas = [p.form for p in default_sort_pokemon(all_records) if p.dex_id == 6]

    assert megas == [None, "Mega Charizard X", "Mega Charizard Y"]


def test_query_module_does_not_import_textual():
    code = "import sys, pokedex_tui.query; sys.exit('textual' in sys.modules)"
    result = subprocess.run([sys.executable, "-c", code], check=False)
    assert result.returncode == 0, "pokedex_tui.query pulled in Textual"


# --- The App -------------------------------------------------------------------


async def test_app_stores_records_as_a_sorted_tuple():
    from pokedex_tui.app import PokedexApp
    from pokedex_tui.query import default_sort_pokemon

    app = PokedexApp()
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        assert isinstance(app.all_records, tuple)
        assert app.all_records == default_sort_pokemon(app.all_records)
