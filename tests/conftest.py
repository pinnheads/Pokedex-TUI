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


# Phase 4 (query layer): hand-made records for the search, filter and sort
# tests. Real stats, listed in Dex order. What each row is there for:
# - single type and dual type: Charmander (Fire), Charizard (Fire/Flying)
# - the same two types in swapped slots: Pelipper (Water/Flying) and
#   Cramorant (Flying/Water)
# - a Mega form (Gen 6) and an Alolan form (Gen 7) of Gen 1 Dex numbers
# - an accent: Flabébé; punctuation: Farfetch'd, Mr. Mime, Type: Null
# - equal Totals on different Dex numbers: Charizard and Type: Null (534);
#   equal Totals on one Dex number: Raichu and Alolan Raichu (485)
# - a Dex number whose only row has a form: Nidoran (Female)
# - "mega" inside a name that is not a Mega: Meganium (starts with it) and
#   Yanmega (only contains it)
QUERY_ROWS = (
    # dex, name, form, type1, type2, (hp, atk, def, spa, spd, spe), total, gen
    (1, "Bulbasaur", None, "Grass", "Poison", (45, 49, 49, 65, 65, 45), 318, 1),
    (4, "Charmander", None, "Fire", None, (39, 52, 43, 60, 50, 65), 309, 1),
    (5, "Charmeleon", None, "Fire", None, (58, 64, 58, 80, 65, 80), 405, 1),
    (6, "Charizard", None, "Fire", "Flying", (78, 84, 78, 109, 85, 100), 534, 1),
    (
        6,
        "Charizard",
        "Mega Charizard X",
        "Fire",
        "Dragon",
        (78, 130, 111, 130, 85, 100),
        634,
        6,
    ),
    (26, "Raichu", None, "Electric", None, (60, 90, 55, 90, 80, 110), 485, 1),
    (
        26,
        "Raichu",
        "Alolan Raichu",
        "Electric",
        "Psychic",
        (60, 85, 50, 95, 85, 110),
        485,
        7,
    ),
    (29, "Nidoran", "Female", "Poison", None, (55, 47, 52, 40, 40, 41), 275, 1),
    (83, "Farfetch'd", None, "Normal", "Flying", (52, 90, 55, 58, 62, 60), 377, 1),
    (122, "Mr. Mime", None, "Psychic", "Fairy", (40, 45, 65, 100, 120, 90), 460, 1),
    (154, "Meganium", None, "Grass", None, (80, 82, 100, 83, 100, 80), 525, 2),
    (279, "Pelipper", None, "Water", "Flying", (60, 50, 100, 95, 70, 65), 440, 3),
    (469, "Yanmega", None, "Bug", "Flying", (86, 76, 86, 116, 56, 95), 515, 4),
    (669, "Flabébé", None, "Fairy", None, (44, 38, 39, 61, 79, 42), 303, 6),
    (772, "Type: Null", None, "Normal", None, (95, 95, 95, 95, 95, 59), 534, 7),
    (845, "Cramorant", None, "Flying", "Water", (70, 85, 55, 85, 95, 85), 475, 8),
)


@pytest.fixture
def query_records(make_pokemon):
    """The 16 QUERY_ROWS as a tuple of Pokemon, in Dex order."""
    records = []
    for dex, name, form, type1, type2, stats, total, gen in QUERY_ROWS:
        hp, attack, defense, sp_atk, sp_def, speed = stats
        records.append(
            make_pokemon(
                dex_id=dex,
                name=name,
                form=form,
                type1=type1,
                type2=type2,
                hp=hp,
                attack=attack,
                defense=defense,
                sp_atk=sp_atk,
                sp_def=sp_def,
                speed=speed,
                total=total,
                generation=gen,
            )
        )
    return tuple(records)
