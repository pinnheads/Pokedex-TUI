"""PTI-100: the default record order lives in query.py, and the App keeps a tuple.

Names these tests expect (rename here if you chose different ones):
- pokedex_tui.query.default_sort_pokemon(records): takes any iterable of
  Pokemon and returns a new tuple in Dex order, base form before its forms.
- PokedexApp.all_records: that tuple, stored once the data has loaded.

C4 (PTI-33): the Total rank lookup, built once at startup.
- pokedex_tui.query.total_ranks(records): takes any iterable of Pokemon and
  returns a read-only mapping from each record's key to its rank by Total,
  highest Total first. Equal Totals share a rank and the next rank skips ahead
  (three tied at #2, then #5).
- PokedexApp.total_ranks: that mapping, built from all the records at startup.
"""

import subprocess
import sys

import pytest

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


# --- total_ranks (C4) -----------------------------------------------------------

# The 14 fixture rows by Total: Zygarde Complete 708, Mega Charizard X 634,
# Zygarde 50% 600, Charizard 534, Zygarde 10% 486, Raichu and Alolan Raichu
# 485 (tied), Mr. Mime 460, Pikachu 320, Bulbasaur 318, Charmander 309,
# Flabebe 303, Nidoran Female 275, Nidoran Male 273.
SMALL_RANKS = {
    ("Zygarde", "Complete Forme"): 1,
    ("Charizard", "Mega Charizard X"): 2,
    ("Zygarde50% Forme", None): 3,
    ("Charizard", None): 4,
    ("Zygarde10% Forme", None): 5,
    ("Raichu", None): 6,
    ("Raichu", "Alolan Raichu"): 6,
    ("Mr. Mime", None): 8,
    ("Pikachu", None): 9,
    ("Bulbasaur", None): 10,
    ("Charmander", None): 11,
    ("Flabébé", None): 12,
    ("Nidoran", "Female"): 13,
    ("Nidoran", "Male"): 14,
}


def test_total_ranks_on_the_small_fixture(small_records):
    from pokedex_tui.query import total_ranks

    ranks = total_ranks(small_records)

    assert {(p.name, p.form): ranks[p.key] for p in small_records} == SMALL_RANKS


def test_tied_totals_share_a_rank_and_the_next_rank_skips(small_records):
    from pokedex_tui.query import total_ranks

    ranks = total_ranks(small_records)
    by_name = {(p.name, p.form): ranks[p.key] for p in small_records}

    assert by_name[("Raichu", None)] == by_name[("Raichu", "Alolan Raichu")] == 6
    assert by_name[("Mr. Mime", None)] == 8
    assert 7 not in ranks.values()


def test_total_ranks_has_one_entry_per_record_keyed_by_key(small_records):
    from pokedex_tui.query import total_ranks

    ranks = total_ranks(small_records)

    assert set(ranks) == {p.key for p in small_records}


def test_total_ranks_does_not_depend_on_input_order(small_records):
    from pokedex_tui.query import total_ranks

    forwards = dict(total_ranks(small_records))
    backwards = dict(total_ranks(iter(list(reversed(small_records)))))

    assert forwards == backwards


def test_total_ranks_is_read_only(small_records):
    from pokedex_tui.query import total_ranks

    ranks = total_ranks(small_records)
    some_key = small_records[0].key

    with pytest.raises(TypeError):
        ranks[some_key] = 99  # type: ignore[index]


def test_total_ranks_of_nothing_is_empty():
    from pokedex_tui.query import total_ranks

    assert len(total_ranks(())) == 0


def test_total_ranks_on_the_real_data(all_records):
    from pokedex_tui.query import total_ranks

    ranks = total_ranks(all_records)
    by_name = {(p.name, p.form): ranks[p.key] for p in all_records}

    assert len(ranks) == 1215
    assert by_name[("Eternatus", "Eternamax")] == 1  # Total 1125, the highest
    # Mega Mewtwo X, Mega Mewtwo Y and Mega Rayquaza tie on 780, then 770.
    assert sorted(ranks.values())[:5] == [1, 2, 2, 2, 5]
    assert (
        by_name[("Charizard", "Mega Charizard X")]
        == by_name[("Charizard", "Mega Charizard Y")]
    )
    assert by_name[("Charizard", None)] > by_name[("Charizard", "Mega Charizard X")]
    assert max(ranks.values()) <= 1215


async def test_app_builds_total_ranks_at_startup():
    from pokedex_tui.app import PokedexApp
    from pokedex_tui.query import total_ranks

    app = PokedexApp()
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        assert len(app.total_ranks) == 1215
        assert dict(app.total_ranks) == dict(total_ranks(app.all_records))


# =============================================================================
# Phase 4: search, filter and sort (PTI-53, 45, 39, 37, 34, 28, 22, 12, 21, 10)
#
# Names these tests expect (rename here if you chose different ones):
# - pokedex_tui.query.normalise(text): the plain form used to compare names
#   and search text. Lower case (case folded), no accents, no punctuation,
#   no spaces at the ends. Spaces inside the text stay, so "Mr. Mime" becomes
#   "mr mime".
# - pokedex_tui.query.filter_and_sort(records, criteria, sort=SortOrder()):
#   the one public entry point. Takes any iterable of Pokemon, returns a new
#   tuple of the matching records in order.
# - pokedex_tui.query.type_options(slot) and generation_options(): the values
#   behind the pickers. None stands for "Any" or "All".
# - pokedex_tui.query.type_counts(records, criteria, slot): for each choice in
#   that type picker, how many records would match if it were picked.
# - pokedex_tui.models.SortOrder and SORT_FIELDS: see test_models.py.
#
# Most tests use query_records, the 16 hand-made rows in conftest.py.
# =============================================================================


def _names(records):
    """(name, form) pairs, so a failing test shows readable rows."""
    return [(p.name, p.form) for p in records]


def _run(records, sort=None, **criteria):
    from pokedex_tui.models import Criteria, SortOrder
    from pokedex_tui.query import filter_and_sort

    return filter_and_sort(records, Criteria(**criteria), sort or SortOrder())


# --- Q1: the module and the entry point (PTI-53) -------------------------------


def test_nothing_in_gives_nothing_out():
    assert _run(()) == ()


def test_result_is_a_tuple(query_records):
    assert isinstance(_run(query_records), tuple)


def test_entry_point_accepts_a_list_and_leaves_it_alone(query_records):
    records = list(query_records)
    before = list(records)

    _run(records, search="char")

    assert records == before


def test_the_sort_argument_can_be_left_out(query_records):
    from pokedex_tui.models import Criteria
    from pokedex_tui.query import filter_and_sort

    assert filter_and_sort(query_records, Criteria()) == query_records


# --- Q2: name normalisation (PTI-45) -------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Flabébé", "flabebe"),
        ("FLABEBE", "flabebe"),
        ("  char  ", "char"),
        ("Mr. Mime", "mr mime"),
        ("mr mime", "mr mime"),
        ("Farfetch'd", "farfetchd"),
        ("Type: Null", "type null"),
        ("Ho-Oh", "hooh"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_normalise(text, expected):
    from pokedex_tui.query import normalise

    assert normalise(text) == expected


def test_normalise_uses_case_folding_not_lower_case():
    from pokedex_tui.query import normalise

    # "ß".lower() is still "ß"; case folding turns it into "ss".
    assert normalise("Straße") == normalise("STRASSE")


# --- Q3: name search (PTI-39) ---------------------------------------------------


def test_search_finds_names_containing_the_text(query_records):
    assert _names(_run(query_records, search="char")) == [
        ("Charmander", None),
        ("Charmeleon", None),
        ("Charizard", None),
        ("Charizard", "Mega Charizard X"),
    ]


def test_search_matches_the_form_name(query_records):
    assert _names(_run(query_records, search="ALOLAN")) == [("Raichu", "Alolan Raichu")]


def test_mega_finds_the_mega_form_and_names_containing_mega(query_records):
    found = _names(_run(query_records, search="mega"))

    assert ("Charizard", "Mega Charizard X") in found
    # Correct substring matches, even though they are not Megas.
    assert ("Meganium", None) in found
    assert ("Yanmega", None) in found
    assert len(found) == 3


@pytest.mark.parametrize("text", ["flabebe", "Flabébé", "FLABEBE"])
def test_search_ignores_accents_and_case(query_records, text):
    assert _names(_run(query_records, search=text)) == [("Flabébé", None)]


@pytest.mark.parametrize(
    ("text", "name"),
    [
        ("mr mime", "Mr. Mime"),
        ("mr. mime", "Mr. Mime"),
        ("farfetchd", "Farfetch'd"),
        ("farfetch'd", "Farfetch'd"),
        ("type null", "Type: Null"),
        ("type: null", "Type: Null"),
    ],
)
def test_search_ignores_punctuation(query_records, text, name):
    assert _names(_run(query_records, search=text)) == [(name, None)]


def test_search_ignores_spaces_at_the_ends(query_records):
    assert _run(query_records, search="  mime  ") == _run(query_records, search="mime")


def test_search_of_only_spaces_returns_everything(query_records):
    assert _run(query_records, search="   ") == query_records


def test_search_that_matches_nothing_returns_an_empty_tuple(query_records):
    assert _run(query_records, search="zzz") == ()


# --- Q4: type filter (PTI-37) ---------------------------------------------------


def test_type_any_any_keeps_everything(query_records):
    assert _run(query_records, type1=None, type2=None) == query_records


def test_one_type_matches_either_slot(query_records):
    # Psychic is Mr. Mime's first type and Alolan Raichu's second.
    expected = [("Raichu", "Alolan Raichu"), ("Mr. Mime", None)]

    assert _names(_run(query_records, type1="Psychic")) == expected
    assert _names(_run(query_records, type2="Psychic")) == expected


def test_two_types_match_in_either_order(query_records):
    expected = [("Pelipper", None), ("Cramorant", None)]

    assert _names(_run(query_records, type1="Water", type2="Flying")) == expected
    assert _names(_run(query_records, type1="Flying", type2="Water")) == expected


def test_the_same_type_twice_counts_as_one(query_records):
    assert _run(query_records, type1="Fire", type2="Fire") == _run(
        query_records, type1="Fire"
    )


def test_a_type_with_no_second_type_gives_pure_single_types(query_records):
    from pokedex_tui.models import NO_SECOND_TYPE

    found = _run(query_records, type1="Fire", type2=NO_SECOND_TYPE)

    assert _names(found) == [("Charmander", None), ("Charmeleon", None)]


def test_any_with_no_second_type_gives_every_single_type(query_records):
    from pokedex_tui.models import NO_SECOND_TYPE

    found = _run(query_records, type1=None, type2=NO_SECOND_TYPE)

    assert all(p.type2 is None for p in found)
    assert len(found) == 7
