"""Shared fixtures for the Phase 1 (data layer) tests."""

from pathlib import Path

import pytest

# Imports from pokedex_tui happen inside the fixtures, so a missing module
# shows up as failing tests rather than one conftest error that hides the rest.

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def small_csv() -> Path:
    """14 hand-picked rows that cover every CSV quirk."""
    return FIXTURES / "pokemon_small.csv"


@pytest.fixture
def broken_csv() -> Path:
    """Valid header, two good rows, then a non-numeric Attack on line 4."""
    return FIXTURES / "pokemon_broken.csv"


@pytest.fixture
def small_records(small_csv):
    from pokedex_tui.loader import load_pokemon

    return load_pokemon(small_csv)


@pytest.fixture(scope="session")
def all_records():
    """The real bundled CSV, loaded once for the whole test run."""
    from pokedex_tui.loader import load_pokemon

    return load_pokemon()


@pytest.fixture
def make_pokemon():
    """Build a Pokemon directly, overriding only the fields a test cares about."""

    from pokedex_tui.models import Pokemon

    def _make(**overrides):
        fields = {
            "dex_id": 6,
            "name": "Charizard",
            "form": None,
            "type1": "Fire",
            "type2": "Flying",
            "hp": 78,
            "attack": 84,
            "defense": 78,
            "sp_atk": 109,
            "sp_def": 85,
            "speed": 100,
            "total": 534,
            "generation": 1,
        }
        fields.update(overrides)
        return Pokemon(**fields)

    return _make
