"""Phase 0: smoke tests proving the skeleton installs, ships its files and runs.

Names these tests expect (rename here if you chose different ones):
- pokedex_tui.app.PokedexApp: the Textual App class.
- A console script called "pokedex-tui" that points at a callable.
"""

import csv
from importlib.metadata import entry_points
from importlib.resources import files

import pytest

EXPECTED_HEADER = [
    "ID",
    "Name",
    "Form",
    "Type1",
    "Type2",
    "Total",
    "HP",
    "Attack",
    "Defense",
    "Sp. Atk",
    "Sp. Def",
    "Speed",
    "Generation",
]

# --- Packaging ---------------------------------------------------------------


def test_package_imports():
    import pokedex_tui

    assert pokedex_tui.__name__ == "pokedex_tui"


def test_bundled_csv_is_package_data():
    csv_file = files("pokedex_tui") / "data" / "Pokemon.csv"

    assert csv_file.is_file()
    with csv_file.open(encoding="utf-8-sig", newline="") as handle:
        assert next(csv.reader(handle)) == EXPECTED_HEADER


def test_bundled_csv_has_all_rows():
    csv_file = files("pokedex_tui") / "data" / "Pokemon.csv"

    with csv_file.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    assert len(rows) == 1 + 1215  # header plus every Pokémon


def test_stylesheet_is_package_data():
    assert (files("pokedex_tui") / "styles" / "app.tcss").is_file()


def test_console_script_points_at_a_callable():
    scripts = entry_points(group="console_scripts", name="pokedex-tui")

    assert len(scripts) == 1, "no 'pokedex-tui' command; check [project.scripts]"
    assert callable(next(iter(scripts)).load())


# --- The app -----------------------------------------------------------------


def test_app_title():
    from pokedex_tui.app import PokedexApp

    assert PokedexApp().title == "Pokédex"


@pytest.mark.asyncio
async def test_app_starts_and_quits_with_q():
    from pokedex_tui.app import PokedexApp

    app = PokedexApp()
    async with app.run_test() as pilot:
        assert app.is_running
        await pilot.press("q")
        await pilot.pause()

    assert app.return_code == 0


@pytest.mark.asyncio
async def test_footer_shows_the_quit_key():
    from textual.widgets import Footer

    from pokedex_tui.app import PokedexApp

    app = PokedexApp()
    async with app.run_test() as pilot:
        await pilot.pause()  # let on_mount push the screens
        app.screen.query_one(Footer)
        keys = {binding.key for _, binding, _, _ in app.active_bindings.values()}
        assert "q" in keys


@pytest.mark.asyncio
async def test_app_starts_from_another_folder(tmp_path, monkeypatch):
    """The stylesheet must be found next to the code, not in the current folder."""
    from pokedex_tui.app import PokedexApp

    monkeypatch.chdir(tmp_path)
    app = PokedexApp()
    async with app.run_test() as pilot:
        await pilot.press("q")
        await pilot.pause()

    assert app.return_code == 0
